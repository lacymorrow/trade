from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from trading.bot import TradingBot
from trading.data_engine import DataEngine
from trading.signal_engine import SignalEngine
from trading.trade_engine import TradeEngine
import threading
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    api_key = db.Column(db.String(128))
    api_secret = db.Column(db.String(128))
    bots = db.relationship('Bot', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Bot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='stopped')  # running, stopped, error
    config = db.Column(db.Text)  # JSON string of bot configuration
    symbols = db.Column(db.Text)  # JSON array of trading symbols
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_config(self):
        return json.loads(self.config) if self.config else {}

    def set_config(self, config_dict):
        self.config = json.dumps(config_dict)

    def get_symbols(self):
        return json.loads(self.symbols) if self.symbols else []

    def set_symbols(self, symbols_list):
        self.symbols = json.dumps(symbols_list)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    side = db.Column(db.String(4), nullable=False)  # buy/sell
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(10), nullable=False)  # open, closed, cancelled
    pnl = db.Column(db.Float)  # Profit/Loss when closed

# Bot instance storage
active_bots = {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_bots = Bot.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', bots=user_bots)

@app.route('/bot/new', methods=['GET', 'POST'])
@login_required
def new_bot():
    if request.method == 'POST':
        name = request.form.get('name')
        symbols = request.form.get('symbols', '').split(',')
        config = {
            'initial_capital': float(request.form.get('initial_capital', 10000)),
            'risk_per_trade': float(request.form.get('risk_per_trade', 0.02)),
            'take_profit': float(request.form.get('take_profit', 0.03)),
            'stop_loss': float(request.form.get('stop_loss', 0.02)),
            'max_positions': int(request.form.get('max_positions', 5)),
            'strategy_params': {
                'trend_weight': float(request.form.get('trend_weight', 0.4)),
                'momentum_weight': float(request.form.get('momentum_weight', 0.3)),
                'sentiment_weight': float(request.form.get('sentiment_weight', 0.3)),
            }
        }

        bot = Bot(
            name=name,
            user_id=current_user.id,
            status='stopped'
        )
        bot.set_config(config)
        bot.set_symbols(symbols)

        db.session.add(bot)
        db.session.commit()

        flash('Bot created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('new_bot.html')

@app.route('/bot/<int:bot_id>')
@login_required
def bot_detail(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    if bot.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    trades = Trade.query.filter_by(bot_id=bot_id).order_by(Trade.timestamp.desc()).limit(50).all()
    return render_template('bot_detail.html', bot=bot, trades=trades)

@app.route('/bot/<int:bot_id>/start')
@login_required
def start_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    if bot.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    if bot.id in active_bots:
        return jsonify({'error': 'Bot is already running'}), 400

    try:
        # Initialize bot components
        data_engine = DataEngine()
        signal_engine = SignalEngine(data_engine)
        trade_engine = TradeEngine(
            api_key=current_user.api_key,
            api_secret=current_user.api_secret
        )

        # Create bot instance with user configuration
        trading_bot = TradingBot(
            config=bot.get_config(),
            data_engine=data_engine,
            signal_engine=signal_engine,
            trade_engine=trade_engine
        )

        # Start bot in a separate thread
        bot_thread = threading.Thread(
            target=trading_bot.run,
            args=(bot.get_symbols(),),
            daemon=True
        )
        bot_thread.start()

        # Store bot instance and thread
        active_bots[bot.id] = {
            'bot': trading_bot,
            'thread': bot_thread
        }

        # Update bot status
        bot.status = 'running'
        db.session.commit()

        return jsonify({'message': 'Bot started successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bot/<int:bot_id>/stop')
@login_required
def stop_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    if bot.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    if bot.id not in active_bots:
        return jsonify({'error': 'Bot is not running'}), 400

    try:
        # Stop the bot
        active_bots[bot.id]['bot'].stop()
        # Wait for thread to finish
        active_bots[bot.id]['thread'].join(timeout=5)
        # Remove bot from active bots
        del active_bots[bot.id]

        # Update bot status
        bot.status = 'stopped'
        db.session.commit()

        return jsonify({'message': 'Bot stopped successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bot/<int:bot_id>/update', methods=['POST'])
@login_required
def update_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    if bot.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    if bot.status == 'running':
        return jsonify({'error': 'Cannot update running bot'}), 400

    try:
        config = bot.get_config()

        # Update configuration
        config['risk_per_trade'] = float(request.form.get('risk_per_trade', config['risk_per_trade']))
        config['take_profit'] = float(request.form.get('take_profit', config['take_profit']))
        config['stop_loss'] = float(request.form.get('stop_loss', config['stop_loss']))
        config['max_positions'] = int(request.form.get('max_positions', config['max_positions']))

        strategy_params = config.get('strategy_params', {})
        strategy_params['trend_weight'] = float(request.form.get('trend_weight', strategy_params.get('trend_weight', 0.4)))
        strategy_params['momentum_weight'] = float(request.form.get('momentum_weight', strategy_params.get('momentum_weight', 0.3)))
        strategy_params['sentiment_weight'] = float(request.form.get('sentiment_weight', strategy_params.get('sentiment_weight', 0.3)))

        config['strategy_params'] = strategy_params
        bot.set_config(config)

        # Update symbols if provided
        symbols = request.form.get('symbols')
        if symbols:
            bot.set_symbols(symbols.split(','))

        db.session.commit()
        return jsonify({'message': 'Bot updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bot/<int:bot_id>/delete')
@login_required
def delete_bot(bot_id):
    bot = Bot.query.get_or_404(bot_id)
    if bot.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    if bot.status == 'running':
        flash('Cannot delete running bot', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(bot)
    db.session.commit()
    flash('Bot deleted successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.api_key = request.form.get('api_key')
        current_user.api_secret = request.form.get('api_secret')
        db.session.commit()
        flash('API credentials updated successfully', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
