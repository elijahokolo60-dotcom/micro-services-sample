"""
New Gen Bank Software Simulation
A modular, event-driven banking pipeline with microservices
"""

import asyncio
import json
import random
import uuid
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from collections import defaultdict
import hashlib

# ==================== DATA MODELS ====================

class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    FEE = "FEE"

class AccountType(Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    BUSINESS = "BUSINESS"
    INVESTMENT = "INVESTMENT"

class TransactionStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    FRAUD_REVIEW = "FRAUD_REVIEW"

@dataclass
class Customer:
    customer_id: str
    name: str
    email: str
    phone: str
    risk_score: float = 0.5
    kyc_status: str = "VERIFIED"
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class Account:
    account_id: str
    customer_id: str
    account_type: AccountType
    balance: float
    currency: str = "USD"
    status: str = "ACTIVE"
    created_at: str = None
    last_updated: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.last_updated = self.created_at

@dataclass
class Transaction:
    transaction_id: str
    account_id: str
    amount: float
    transaction_type: TransactionType
    status: TransactionStatus
    description: str
    counterparty_account: Optional[str] = None
    timestamp: str = None
    location: Optional[Dict] = None
    device_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class FraudAlert:
    alert_id: str
    transaction_id: str
    score: float
    reasons: List[str]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

# ==================== EVENT SYSTEM ====================

class EventType(Enum):
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_PROCESSED = "transaction_processed"
    FRAUD_DETECTED = "fraud_detected"
    CUSTOMER_CREATED = "customer_created"
    ACCOUNT_UPDATED = "account_updated"
    REAL_TIME_NOTIFICATION = "real_time_notification"

@dataclass
class Event:
    event_id: str
    event_type: EventType
    payload: Dict[str, Any]
    timestamp: str = None
    source: str = "banking_pipeline"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if not self.event_id:
            self.event_id = str(uuid.uuid4())

class EventBus:
    """Event-driven message bus for microservices communication"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_history = []
        
    def subscribe(self, event_type: EventType, callback):
        """Subscribe to specific event types"""
        self.subscribers[event_type].append(callback)
        
    def publish(self, event: Event):
        """Publish event to all subscribers"""
        self.event_history.append(event)
        print(f"📡 Event Published: {event.event_type.value} | ID: {event.event_id[:8]}")
        
        # Notify all subscribers asynchronously
        for callback in self.subscribers.get(event.event_type, []):
            asyncio.create_task(callback(event))
            
    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Retrieve events by type"""
        return [e for e in self.event_history if e.event_type == event_type]

# ==================== MICROSERVICES ====================

class Microservice(ABC):
    """Base class for all microservices"""
    
    def __init__(self, name: str, event_bus: EventBus):
        self.name = name
        self.event_bus = event_bus
        self.setup_subscriptions()
        
    @abstractmethod
    def setup_subscriptions(self):
        """Setup event subscriptions"""
        pass

class CustomerOnboardingService(Microservice):
    """Handles customer creation and KYC"""
    
    def __init__(self, event_bus: EventBus):
        super().__init__("customer_onboarding", event_bus)
        self.customers = {}
        
    def setup_subscriptions(self):
        # Could subscribe to KYC verification events
        pass
    
    async def create_customer(self, name: str, email: str, phone: str) -> Customer:
        """Create new customer with KYC check"""
        customer_id = f"CUST-{uuid.uuid4().hex[:8].upper()}"
        
        # Simulate KYC check
        kyc_status = "VERIFIED" if random.random() > 0.1 else "PENDING"
        risk_score = random.uniform(0.1, 0.9)
        
        customer = Customer(
            customer_id=customer_id,
            name=name,
            email=email,
            phone=phone,
            risk_score=risk_score,
            kyc_status=kyc_status
        )
        
        self.customers[customer_id] = customer
        
        # Publish event
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.CUSTOMER_CREATED,
            payload=asdict(customer)
        )
        self.event_bus.publish(event)
        
        print(f"👤 Customer Created: {name} | ID: {customer_id} | Risk: {risk_score:.2f}")
        return customer

class AccountService(Microservice):
    """Manages bank accounts"""
    
    def __init__(self, event_bus: EventBus):
        super().__init__("account_service", event_bus)
        self.accounts = {}
        
    def setup_subscriptions(self):
        self.event_bus.subscribe(EventType.CUSTOMER_CREATED, self.handle_customer_created)
        
    async def handle_customer_created(self, event: Event):
        """Automatically create checking account for new customers"""
        customer_data = event.payload
        await self.create_account(
            customer_id=customer_data['customer_id'],
            account_type=AccountType.CHECKING,
            initial_balance=100.0  # Welcome bonus
        )
    
    async def create_account(self, customer_id: str, account_type: AccountType, initial_balance: float = 0.0) -> Account:
        """Create new bank account"""
        account_id = f"ACC-{account_type.value[:3]}-{uuid.uuid4().hex[:6].upper()}"
        
        account = Account(
            account_id=account_id,
            customer_id=customer_id,
            account_type=account_type,
            balance=initial_balance
        )
        
        self.accounts[account_id] = account
        
        # Publish event
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ACCOUNT_UPDATED,
            payload=asdict(account)
        )
        self.event_bus.publish(event)
        
        print(f"🏦 Account Created: {account_id} | Type: {account_type.value} | Balance: ${initial_balance:.2f}")
        return account
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """Retrieve account by ID"""
        return self.accounts.get(account_id)
    
    async def update_balance(self, account_id: str, amount: float) -> bool:
        """Update account balance"""
        account = self.get_account(account_id)
        if not account:
            return False
            
        account.balance += amount
        account.last_updated = datetime.now().isoformat()
        
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ACCOUNT_UPDATED,
            payload=asdict(account)
        )
        self.event_bus.publish(event)
        
        return True

class FraudDetectionService(Microservice):
    """AI-powered fraud detection using machine learning patterns"""
    
    def __init__(self, event_bus: EventBus):
        super().__init__("fraud_detection", event_bus)
        self.transaction_history = defaultdict(list)
        self.alerts = []
        
    def setup_subscriptions(self):
        self.event_bus.subscribe(EventType.TRANSACTION_CREATED, self.analyze_transaction)
        
    async def analyze_transaction(self, event: Event):
        """Analyze transaction for fraud patterns"""
        transaction_data = event.payload
        transaction_id = transaction_data['transaction_id']
        
        # Simulate ML model analysis
        fraud_score = self.calculate_fraud_score(transaction_data)
        
        if fraud_score > 0.7:
            reasons = self.get_fraud_reasons(transaction_data, fraud_score)
            
            alert = FraudAlert(
                alert_id=f"ALERT-{uuid.uuid4().hex[:8]}",
                transaction_id=transaction_id,
                score=fraud_score,
                reasons=reasons
            )
            
            self.alerts.append(alert)
            
            # Publish fraud alert
            fraud_event = Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.FRAUD_DETECTED,
                payload=asdict(alert)
            )
            self.event_bus.publish(fraud_event)
            
            print(f"🚨 Fraud Alert: Score {fraud_score:.2f} | Reasons: {', '.join(reasons)}")
            
            # Update transaction status
            return TransactionStatus.FRAUD_REVIEW
        
        return TransactionStatus.PENDING
    
    def calculate_fraud_score(self, transaction: Dict) -> float:
        """Calculate fraud probability using simulated ML features"""
        score = 0.0
        
        # Feature 1: Large amount
        amount = transaction['amount']
        if amount > 10000:
            score += 0.3
        elif amount > 5000:
            score += 0.2
            
        # Feature 2: Unusual time (simulate)
        hour = datetime.fromisoformat(transaction['timestamp']).hour
        if hour < 5 or hour > 23:  # Unusual hours
            score += 0.2
            
        # Feature 3: Velocity check (simulate)
        account_id = transaction['account_id']
        recent_tx_count = len([tx for tx in self.transaction_history.get(account_id, []) 
                              if datetime.fromisoformat(tx['timestamp']) > 
                              datetime.now() - timedelta(hours=1)])
        
        if recent_tx_count > 5:
            score += 0.3
            
        # Add some randomness to simulate ML uncertainty
        score += random.uniform(-0.1, 0.1)
        return min(max(score, 0.0), 1.0)
    
    def get_fraud_reasons(self, transaction: Dict, score: float) -> List[str]:
        """Generate reasons for fraud alert"""
        reasons = []
        amount = transaction['amount']
        
        if amount > 10000:
            reasons.append("Large transaction amount")
        if amount > 5000 and random.random() > 0.5:
            reasons.append("Unusual transaction pattern")
        if score > 0.8:
            reasons.append("High risk profile match")
            
        return reasons if reasons else ["Suspicious activity detected"]

class TransactionService(Microservice):
    """Core transaction processing engine"""
    
    def __init__(self, event_bus: EventBus, account_service: AccountService, fraud_service: FraudDetectionService):
        super().__init__("transaction_service", event_bus)
        self.account_service = account_service
        self.fraud_service = fraud_service
        self.transactions = {}
        
    def setup_subscriptions(self):
        self.event_bus.subscribe(EventType.FRAUD_DETECTED, self.handle_fraud_alert)
        
    async def create_transaction(self, account_id: str, amount: float, 
                                transaction_type: TransactionType, 
                                description: str, **kwargs) -> Transaction:
        """Create and process new transaction"""
        
        # Validate account exists
        account = self.account_service.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Check sufficient funds for withdrawals
        if transaction_type in [TransactionType.WITHDRAWAL, TransactionType.TRANSFER, TransactionType.PAYMENT]:
            if account.balance < amount:
                raise ValueError("Insufficient funds")
        
        # Create transaction
        transaction = Transaction(
            transaction_id=f"TX-{uuid.uuid4().hex[:12].upper()}",
            account_id=account_id,
            amount=amount,
            transaction_type=transaction_type,
            status=TransactionStatus.PENDING,
            description=description,
            counterparty_account=kwargs.get('counterparty_account'),
            location=kwargs.get('location'),
            device_id=kwargs.get('device_id')
        )
        
        self.transactions[transaction.transaction_id] = transaction
        
        # Publish transaction created event
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.TRANSACTION_CREATED,
            payload=asdict(transaction)
        )
        self.event_bus.publish(event)
        
        print(f"💳 Transaction Created: {transaction.transaction_id} | Amount: ${amount:.2f} | Type: {transaction_type.value}")
        
        # Process through fraud detection
        fraud_status = await self.fraud_service.analyze_transaction(event)
        
        if fraud_status == TransactionStatus.FRAUD_REVIEW:
            transaction.status = TransactionStatus.FRAUD_REVIEW
            print(f"⏸️ Transaction {transaction.transaction_id} held for fraud review")
            return transaction
        
        # Process transaction if no fraud detected
        await self.process_transaction(transaction)
        return transaction
    
    async def process_transaction(self, transaction: Transaction):
        """Execute the transaction"""
        try:
            account = self.account_service.get_account(transaction.account_id)
            
            # Update balance based on transaction type
            if transaction.transaction_type in [TransactionType.DEPOSIT]:
                await self.account_service.update_balance(transaction.account_id, transaction.amount)
            else:  # Withdrawal, Transfer, Payment
                await self.account_service.update_balance(transaction.account_id, -transaction.amount)
            
            transaction.status = TransactionStatus.COMPLETED
            
            # Publish processed event
            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.TRANSACTION_PROCESSED,
                payload=asdict(transaction)
            )
            self.event_bus.publish(event)
            
            # Send real-time notification
            notification_event = Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.REAL_TIME_NOTIFICATION,
                payload={
                    "type": "transaction_completed",
                    "transaction_id": transaction.transaction_id,
                    "amount": transaction.amount,
                    "account_id": transaction.account_id,
                    "new_balance": account.balance
                }
            )
            self.event_bus.publish(notification_event)
            
            print(f"✅ Transaction Completed: {transaction.transaction_id} | New Balance: ${account.balance:.2f}")
            
        except Exception as e:
            transaction.status = TransactionStatus.FAILED
            print(f"❌ Transaction Failed: {transaction.transaction_id} | Error: {str(e)}")
    
    async def handle_fraud_alert(self, event: Event):
        """Handle fraud alert events"""
        alert_data = event.payload
        transaction_id = alert_data['transaction_id']
        
        if transaction_id in self.transactions:
            transaction = self.transactions[transaction_id]
            print(f"🛡️ Fraud handling for transaction {transaction_id}")
            # In real system, this would trigger manual review workflow

class AnalyticsService(Microservice):
    """Real-time analytics and reporting"""
    
    def __init__(self, event_bus: EventBus):
        super().__init__("analytics_service", event_bus)
        self.metrics = {
            "transactions_processed": 0,
            "fraud_alerts": 0,
            "total_volume": 0.0,
            "active_accounts": 0
        }
        
    def setup_subscriptions(self):
        self.event_bus.subscribe(EventType.TRANSACTION_PROCESSED, self.track_transaction)
        self.event_bus.subscribe(EventType.FRAUD_DETECTED, self.track_fraud)
        self.event_bus.subscribe(EventType.ACCOUNT_UPDATED, self.track_account)
    
    async def track_transaction(self, event: Event):
        self.metrics["transactions_processed"] += 1
        self.metrics["total_volume"] += event.payload.get('amount', 0)
    
    async def track_fraud(self, event: Event):
        self.metrics["fraud_alerts"] += 1
    
    async def track_account(self, event: Event):
        # Simplified active account tracking
        self.metrics["active_accounts"] = len(set(
            tx['account_id'] for tx in self.event_bus.get_events_by_type(EventType.TRANSACTION_PROCESSED)
        ))
    
    def get_dashboard_data(self) -> Dict:
        """Generate analytics dashboard data"""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics,
            "transactions_last_hour": self.metrics["transactions_processed"],
            "fraud_rate": self.metrics["fraud_alerts"] / max(self.metrics["transactions_processed"], 1),
            "avg_transaction_value": self.metrics["total_volume"] / max(self.metrics["transactions_processed"], 1)
        }

class NotificationService(Microservice):
    """Real-time notification system"""
    
    def __init__(self, event_bus: EventBus):
        super().__init__("notification_service", event_bus)
        
    def setup_subscriptions(self):
        self.event_bus.subscribe(EventType.REAL_TIME_NOTIFICATION, self.send_notification)
        self.event_bus.subscribe(EventType.FRAUD_DETECTED, self.send_fraud_alert)
    
    async def send_notification(self, event: Event):
        """Send real-time notifications"""
        payload = event.payload
        notification_type = payload.get('type', 'generic')
        
        if notification_type == 'transaction_completed':
            message = f"Transaction completed: ${payload['amount']:.2f}. New balance: ${payload['new_balance']:.2f}"
            print(f"📱 Push Notification: {message}")
            
            # In real system, would send to mobile app, email, SMS, etc.
    
    async def send_fraud_alert(self, event: Event):
        """Send fraud alerts to security team"""
        alert_data = event.payload
        message = f"🚨 FRAUD ALERT: Score {alert_data['score']:.2f} for transaction {alert_data['transaction_id']}"
        print(f"🔔 Security Alert: {message}")

# ==================== API GATEWAY ====================

class APIGateway:
    """REST API Gateway for external consumers"""
    
    def __init__(self, transaction_service: TransactionService, account_service: AccountService):
        self.transaction_service = transaction_service
        self.account_service = account_service
    
    async def deposit(self, account_id: str, amount: float, description: str = "Deposit"):
        """API endpoint for deposits"""
        return await self.transaction_service.create_transaction(
            account_id=account_id,
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            description=description
        )
    
    async def withdraw(self, account_id: str, amount: float, description: str = "Withdrawal"):
        """API endpoint for withdrawals"""
        return await self.transaction_service.create_transaction(
            account_id=account_id,
            amount=amount,
            transaction_type=TransactionType.WITHDRAWAL,
            description=description
        )
    
    async def transfer(self, from_account: str, to_account: str, amount: float, description: str = "Transfer"):
        """API endpoint for transfers"""
        return await self.transaction_service.create_transaction(
            account_id=from_account,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            description=description,
            counterparty_account=to_account
        )
    
    def get_account_balance(self, account_id: str) -> Optional[float]:
        """API endpoint to get account balance"""
        account = self.account_service.get_account(account_id)
        return account.balance if account else None

# ==================== SIMULATION ====================

async def run_banking_simulation():
    """Run a complete simulation of the new gen banking pipeline"""
    print("\n" + "="*60)
    print("🚀 NEW GEN BANKING SOFTWARE SIMULATION")
    print("="*60 + "\n")
    
    # Initialize event bus
    event_bus = EventBus()
    
    # Initialize microservices
    customer_service = CustomerOnboardingService(event_bus)
    account_service = AccountService(event_bus)
    fraud_service = FraudDetectionService(event_bus)
    transaction_service = TransactionService(event_bus, account_service, fraud_service)
    analytics_service = AnalyticsService(event_bus)
    notification_service = NotificationService(event_bus)
    
    # Initialize API Gateway
    api_gateway = APIGateway(transaction_service, account_service)
    
    # Simulation Steps
    print("1. CUSTOMER ONBOARDING")
    print("-"*40)
    
    # Create customers
    customer1 = await customer_service.create_customer("John Doe", "john@example.com", "+1234567890")
    await asyncio.sleep(0.1)  # Simulate async processing
    
    customer2 = await customer_service.create_customer("Jane Smith", "jane@example.com", "+0987654321")
    await asyncio.sleep(0.1)
    
    print("\n2. ACCOUNT CREATION & INITIAL DEPOSITS")
    print("-"*40)
    
    # Get accounts (created automatically during customer creation)
    accounts = list(account_service.accounts.values())
    account1 = accounts[0] if len(accounts) > 0 else None
    account2 = accounts[1] if len(accounts) > 1 else None
    
    if account1 and account2:
        print(f"Account 1: {account1.account_id} | Balance: ${account1.balance:.2f}")
        print(f"Account 2: {account2.account_id} | Balance: ${account2.balance:.2f}")
        
        print("\n3. TRANSACTION PROCESSING")
        print("-"*40)
        
        # Simulate various transactions
        transactions = []
        
        # Normal deposit
        tx1 = await api_gateway.deposit(account1.account_id, 1500.00, "Salary deposit")
        transactions.append(tx1)
        await asyncio.sleep(0.2)
        
        # Normal withdrawal
        tx2 = await api_gateway.withdraw(account1.account_id, 200.00, "ATM withdrawal")
        transactions.append(tx2)
        await asyncio.sleep(0.2)
        
        # Transfer between accounts
        tx3 = await api_gateway.transfer(account1.account_id, account2.account_id, 300.00, "Rent payment")
        transactions.append(tx3)
        await asyncio.sleep(0.2)
        
        # Large transaction (might trigger fraud detection)
        tx4 = await api_gateway.deposit(account2.account_id, 12000.00, "Large business deposit")
        transactions.append(tx4)
        await asyncio.sleep(0.2)
        
        # Multiple rapid transactions (might trigger velocity check)
        for i in range(3):
            tx = await api_gateway.withdraw(account1.account_id, 50.00, f"Quick withdrawal {i+1}")
            transactions.append(tx)
            await asyncio.sleep(0.1)
        
        print("\n4. ANALYTICS & REPORTING")
        print("-"*40)
        
        # Wait for all events to be processed
        await asyncio.sleep(1)
        
        # Show analytics dashboard
        dashboard = analytics_service.get_dashboard_data()
        print(f"📊 Analytics Dashboard:")
        print(f"   Total Transactions: {dashboard['metrics']['transactions_processed']}")
        print(f"   Fraud Alerts: {dashboard['metrics']['fraud_alerts']}")
        print(f"   Total Volume: ${dashboard['metrics']['total_volume']:.2f}")
        print(f"   Fraud Rate: {dashboard['fraud_rate']:.2%}")
        print(f"   Avg Transaction: ${dashboard['avg_transaction_value']:.2f}")
        
        print("\n5. FINAL ACCOUNT STATUS")
        print("-"*40)
        
        # Final balances
        account1_final = account_service.get_account(account1.account_id)
        account2_final = account_service.get_account(account2.account_id)
        
        print(f"Account {account1_final.account_id}:")
        print(f"  Type: {account1_final.account_type.value}")
        print(f"  Balance: ${account1_final.balance:.2f}")
        print(f"  Last Updated: {account1_final.last_updated[:19]}")
        
        print(f"\nAccount {account2_final.account_id}:")
        print(f"  Type: {account2_final.account_type.value}")
        print(f"  Balance: ${account2_final.balance:.2f}")
        print(f"  Last Updated: {account2_final.last_updated[:19]}")
        
        print("\n6. EVENT BUS STATISTICS")
        print("-"*40)
        
        # Event statistics
        event_types = {}
        for event in event_bus.event_history:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        for event_type, count in event_types.items():
            print(f"  {event_type.value}: {count} events")
        
        print(f"\n  Total Events: {len(event_bus.event_history)}")
    
    print("\n" + "="*60)
    print("🎯 SIMULATION COMPLETE")
    print("="*60)

# ==================== TESTING UTILITIES ====================

def generate_sample_data():
    """Generate sample data for testing"""
    customers = []
    accounts = []
    
    # Generate sample customers
    names = ["Alice Johnson", "Bob Williams", "Charlie Brown", "Diana Prince"]
    for i, name in enumerate(names):
        customer = Customer(
            customer_id=f"CUST-{i+1:04d}",
            name=name,
            email=f"{name.lower().replace(' ', '.')}@example.com",
            phone=f"+1-555-{1000+i:04d}",
            risk_score=random.uniform(0.1, 0.8)
        )
        customers.append(customer)
    
    # Generate sample accounts
    for i, customer in enumerate(customers):
        for acc_type in [AccountType.CHECKING, AccountType.SAVINGS]:
            account = Account(
                account_id=f"ACC-{acc_type.value[:3]}-{i+1:04d}",
                customer_id=customer.customer_id,
                account_type=acc_type,
                balance=random.uniform(1000, 50000)
            )
            accounts.append(account)
    
    return customers, accounts

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Run the simulation
    asyncio.run(run_banking_simulation())
    
    # Example of generating sample data
    print("\n📋 SAMPLE DATA GENERATION")
    print("-"*40)
    
    customers, accounts = generate_sample_data()
    print(f"Generated {len(customers)} customers and {len(accounts)} accounts")
    print(f"\nSample Customer: {customers[0].name} ({customers[0].customer_id})")
    print(f"Sample Account: {accounts[0].account_id} - ${accounts[0].balance:.2f}")