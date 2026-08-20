"""
Smart Warehouse Management & Autonomous Fleet Simulation System
---------------------------------------------------------------
Features:
1. Automated Inventory & Rack Management (SKUs, Locations, Thresholds, Reordering)
2. Autonomous Guided Vehicle (AGV) Fleet Controller (Battery, Tasks, Movement)
3. Dynamic Order Fulfillment Pipeline (Queueing, Dispatching, Status Tracking)
4. Real-time Visual Terminal Dashboard with ASCII/ANSI formatting
5. Automated Event Simulation Engine & Interactive CLI
"""

import time
import random
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional

# Force UTF-8 encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- Color Constants for Terminal UI ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# --- Enums ---
class RobotStatus(Enum):
    IDLE = "IDLE"
    MOVING_TO_SHELF = "MOVING_TO_SHELF"
    PICKING = "PICKING"
    DELIVERING = "DELIVERING"
    CHARGING = "CHARGING"
    MAINTENANCE = "MAINTENANCE"

class OrderStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"

# --- Data Structures ---
@dataclass
class Item:
    sku: str
    name: str
    category: str
    quantity: int
    reorder_level: int
    unit_price: float
    shelf_location: str  # e.g., "A-10", "B-05"

@dataclass
class AGVRobot:
    robot_id: str
    battery: int  # 0 to 100%
    status: RobotStatus = RobotStatus.IDLE
    current_location: str = "CHARGING_BAY"
    current_order_id: Optional[str] = None
    target_location: Optional[str] = None

@dataclass
class Order:
    order_id: str
    sku: str
    quantity: int
    customer_name: str
    status: OrderStatus = OrderStatus.PENDING
    assigned_robot_id: Optional[str] = None

# --- Core Warehouse Controller ---
class SmartWarehouse:
    def __init__(self, name: str = "Apex Logistics Hub"):
        self.name = name
        self.inventory: Dict[str, Item] = {}
        self.fleet: Dict[str, AGVRobot] = {}
        self.orders: List[Order] = []
        self.logs: List[str] = []
        self.total_revenue: float = 0.0
        self.fulfilled_orders_count: int = 0
        self._init_default_data()

    def log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        prefix = {
            "INFO": f"{Colors.OKCYAN}[INFO]{Colors.ENDC}",
            "SUCCESS": f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC}",
            "WARN": f"{Colors.WARNING}[WARN]{Colors.ENDC}",
            "ERROR": f"{Colors.FAIL}[ERROR]{Colors.ENDC}",
            "AGV": f"{Colors.OKBLUE}[AGV FLEET]{Colors.ENDC}"
        }.get(level, f"[{level}]")
        self.logs.append(f"{timestamp} {prefix} {message}")
        if len(self.logs) > 10:
            self.logs.pop(0)

    def _init_default_data(self):
        # Initial Inventory
        default_items = [
            Item("SKU-101", "High-Speed Microcontroller", "Electronics", 45, 10, 24.99, "A-01"),
            Item("SKU-102", "LiPo Battery Pack 5000mAh", "Electronics", 12, 15, 49.50, "A-02"),
            Item("SKU-103", "Precision Servo Motor", "Robotics", 60, 20, 18.75, "B-01"),
            Item("SKU-104", "Carbon Fiber Chassis Unit", "Hardware", 8, 10, 120.00, "B-02"),
            Item("SKU-105", "Optical Lidar Sensor", "Sensors", 25, 5, 185.00, "C-01"),
            Item("SKU-106", "Ultrasonic Distance Sensor", "Sensors", 90, 25, 8.50, "C-02"),
        ]
        for item in default_items:
            self.inventory[item.sku] = item

        # Initial AGV Fleet
        default_robots = [
            AGVRobot("AGV-Alpha", 95, RobotStatus.IDLE, "DOCK-1"),
            AGVRobot("AGV-Beta", 82, RobotStatus.IDLE, "DOCK-2"),
            AGVRobot("AGV-Gamma", 28, RobotStatus.CHARGING, "CHARGING_BAY"),
            AGVRobot("AGV-Delta", 100, RobotStatus.IDLE, "DOCK-3"),
        ]
        for bot in default_robots:
            self.fleet[bot.robot_id] = bot

        self.log("Smart Warehouse System initialized with 6 items & 4 AGVs.", "SUCCESS")

    def add_order(self, sku: str, quantity: int, customer: str) -> Optional[Order]:
        if sku not in self.inventory:
            self.log(f"Order failed: SKU '{sku}' not found in inventory.", "ERROR")
            return None
        
        item = self.inventory[sku]
        if item.quantity < quantity:
            self.log(f"Order failed: Insufficient stock for {item.name} (Req: {quantity}, Available: {item.quantity}).", "WARN")
            return None

        order_id = f"ORD-{random.randint(1000, 9999)}"
        new_order = Order(order_id=order_id, sku=sku, quantity=quantity, customer_name=customer)
        self.orders.append(new_order)
        self.log(f"New order placed: {order_id} ({quantity}x {item.name}) for {customer}.", "INFO")
        return new_order

    def dispatch_agv(self):
        """Match pending orders with available IDLE AGVs."""
        pending_orders = [o for o in self.orders if o.status == OrderStatus.PENDING]
        idle_robots = [r for r in self.fleet.values() if r.status == RobotStatus.IDLE and r.battery > 20]

        for order in pending_orders:
            if not idle_robots:
                break
            
            robot = idle_robots.pop(0)
            item = self.inventory[order.sku]

            # Assign order to robot
            order.status = OrderStatus.PROCESSING
            order.assigned_robot_id = robot.robot_id

            robot.status = RobotStatus.MOVING_TO_SHELF
            robot.current_order_id = order.order_id
            robot.target_location = item.shelf_location

            self.log(f"Dispatched {robot.robot_id} to shelf {item.shelf_location} for Order {order.order_id}.", "AGV")

    def tick_simulation(self):
        """Advance warehouse simulation by 1 cycle."""
        # 1. Update AGVs
        for robot in list(self.fleet.values()):
            if robot.status == RobotStatus.CHARGING:
                robot.battery = min(100, robot.battery + 15)
                if robot.battery >= 95:
                    robot.status = RobotStatus.IDLE
                    robot.current_location = "DOCK-READY"
                    self.log(f"{robot.robot_id} fully charged and ready.", "AGV")

            elif robot.status == RobotStatus.MOVING_TO_SHELF:
                robot.battery -= random.randint(1, 3)
                robot.current_location = robot.target_location
                robot.status = RobotStatus.PICKING
                self.log(f"{robot.robot_id} reached {robot.current_location}. Picking items...", "AGV")

            elif robot.status == RobotStatus.PICKING:
                robot.status = RobotStatus.DELIVERING
                robot.target_location = "PACKING_BAY"
                self.log(f"{robot.robot_id} picked payload. Transporting to PACKING_BAY.", "AGV")

            elif robot.status == RobotStatus.DELIVERING:
                robot.battery -= random.randint(2, 4)
                robot.current_location = "PACKING_BAY"

                # Complete order
                if robot.current_order_id:
                    order = next((o for o in self.orders if o.order_id == robot.current_order_id), None)
                    if order:
                        order.status = OrderStatus.FULFILLED
                        item = self.inventory[order.sku]
                        item.quantity -= order.quantity
                        self.total_revenue += item.unit_price * order.quantity
                        self.fulfilled_orders_count += 1
                        self.log(f"Order {order.order_id} FULFILLED! Stock for {item.name} is now {item.quantity}.", "SUCCESS")

                robot.current_order_id = None
                robot.target_location = None
                
                # Check battery status
                if robot.battery < 25:
                    robot.status = RobotStatus.CHARGING
                    robot.current_location = "CHARGING_BAY"
                    self.log(f"{robot.robot_id} battery low ({robot.battery}%). Heading to CHARGING_BAY.", "WARN")
                else:
                    robot.status = RobotStatus.IDLE

        # 2. Try dispatching pending orders
        self.dispatch_agv()

    def restock_item(self, sku: str, qty: int):
        if sku in self.inventory:
            self.inventory[sku].quantity += qty
            self.log(f"Restocked {qty} units of {self.inventory[sku].name} (Total: {self.inventory[sku].quantity}).", "SUCCESS")
        else:
            self.log(f"Restock failed: SKU {sku} not found.", "ERROR")

    def render_dashboard(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*75}")
        print(f"   [+] SMART WAREHOUSE MANAGEMENT SYSTEM & AGV FLEET CONTROL [+]   ")
        print(f"{'='*75}{Colors.ENDC}")

        # Overview Metrics
        avg_battery = sum(r.battery for r in self.fleet.values()) / max(1, len(self.fleet))
        low_stock_count = sum(1 for item in self.inventory.values() if item.quantity <= item.reorder_level)
        
        print(f"{Colors.BOLD}SYSTEM SUMMARY:{Colors.ENDC}")
        print(f" Revenue: {Colors.OKGREEN}${self.total_revenue:,.2f}{Colors.ENDC} | "
              f" Fulfilled Orders: {Colors.OKBLUE}{self.fulfilled_orders_count}{Colors.ENDC} | "
              f" Avg AGV Battery: {Colors.OKCYAN}{avg_battery:.1f}%{Colors.ENDC} | "
              f" Low Stock Alerts: {Colors.WARNING}{low_stock_count}{Colors.ENDC}\n")

        # AGV Fleet Table
        print(f"{Colors.BOLD}AGV FLEET STATUS:{Colors.ENDC}")
        print(f"{'ID':<12} | {'Battery':<10} | {'Status':<18} | {'Current Location':<15} | {'Active Task'}")
        print("-" * 75)
        for r in self.fleet.values():
            bat_color = Colors.OKGREEN if r.battery > 50 else (Colors.WARNING if r.battery > 20 else Colors.FAIL)
            status_color = Colors.OKCYAN if r.status == RobotStatus.IDLE else (Colors.WARNING if r.status == RobotStatus.CHARGING else Colors.OKGREEN)
            task_str = f"Order {r.current_order_id}" if r.current_order_id else "None"
            print(f"{r.robot_id:<12} | {bat_color}{r.battery:>3}%{Colors.ENDC}      | {status_color}{r.status.value:<18}{Colors.ENDC} | {r.current_location:<15} | {task_str}")

        print("\n" + f"{Colors.BOLD}INVENTORY RACK STATUS:{Colors.ENDC}")
        print(f"{'SKU':<10} | {'Item Name':<28} | {'Loc':<6} | {'Qty':<6} | {'Status':<10} | {'Price'}")
        print("-" * 75)
        for item in self.inventory.values():
            stock_status = f"{Colors.FAIL}LOW STOCK{Colors.ENDC}" if item.quantity <= item.reorder_level else f"{Colors.OKGREEN}OK{Colors.ENDC}"
            print(f"{item.sku:<10} | {item.name:<28} | {item.shelf_location:<6} | {item.quantity:<6} | {stock_status:<19} | ${item.unit_price:.2f}")

        # Recent Log Console
        print("\n" + f"{Colors.BOLD}SYSTEM ACTIVITY LOGS:{Colors.ENDC}")
        print("-" * 75)
        for log_entry in self.logs[-6:]:
            print(f" {log_entry}")
        print("=" * 75)


def run_automated_demo(warehouse: SmartWarehouse, cycles: int = 12):
    """Runs a real-time animated simulation demo of the smart warehouse."""
    warehouse.log("Starting automated simulation demo mode...", "INFO")
    
    # Pre-populate some orders
    warehouse.add_order("SKU-101", 2, "Tesla Gigafactory")
    warehouse.add_order("SKU-102", 5, "Amazon Robotics Lab")
    warehouse.add_order("SKU-105", 1, "Boston Dynamics")
    
    customers = ["Apple Operations", "SpaceX Hub", "Toyota Auto", "Intel Corp", "NVIDIA AI Lab"]
    skus = list(warehouse.inventory.keys())

    for i in range(1, cycles + 1):
        # Randomly inject new orders or restocks
        if random.random() < 0.6:
            random_sku = random.choice(skus)
            random_qty = random.randint(1, 4)
            random_cust = random.choice(customers)
            warehouse.add_order(random_sku, random_qty, random_cust)
        
        if random.random() < 0.2:
            random_sku = random.choice(skus)
            warehouse.restock_item(random_sku, random.randint(10, 25))

        warehouse.tick_simulation()
        warehouse.render_dashboard()
        print(f"\n{Colors.OKCYAN}[DEMO MODE] Running Simulation Cycle {i}/{cycles}... (Press Ctrl+C to stop){Colors.ENDC}")
        time.sleep(1.0)


def main():
    warehouse = SmartWarehouse()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        try:
            run_automated_demo(warehouse)
        except KeyboardInterrupt:
            print("\nDemo interrupted by user.")
        return

    # Interactive Menu
    while True:
        warehouse.render_dashboard()
        print(f"\n{Colors.BOLD}MAIN MENU OPTIONS:{Colors.ENDC}")
        print(" [1] Step Simulation Cycle (1 Tick)")
        print(" [2] Run Automated Real-Time Demo (12 Cycles)")
        print(" [3] Place New Order")
        print(" [4] Restock Inventory SKU")
        print(" [5] Add Custom AGV Robot to Fleet")
        print(" [6] Exit System")

        choice = input("\nSelect Option [1-6]: ").strip()

        if choice == "1":
            warehouse.tick_simulation()
        elif choice == "2":
            try:
                run_automated_demo(warehouse, cycles=15)
            except KeyboardInterrupt:
                pass
        elif choice == "3":
            print("\n--- Place New Order ---")
            sku = input("Enter SKU (e.g. SKU-101): ").strip().upper()
            try:
                qty = int(input("Enter Quantity: ").strip())
                cust = input("Enter Customer Name: ").strip()
                warehouse.add_order(sku, qty, cust)
            except ValueError:
                warehouse.log("Invalid quantity input.", "ERROR")
        elif choice == "4":
            print("\n--- Restock SKU ---")
            sku = input("Enter SKU to Restock (e.g. SKU-102): ").strip().upper()
            try:
                qty = int(input("Enter Restock Quantity: ").strip())
                warehouse.restock_item(sku, qty)
            except ValueError:
                warehouse.log("Invalid restock quantity.", "ERROR")
        elif choice == "5":
            bot_name = input("Enter AGV Name (e.g. AGV-Epsilon): ").strip()
            if bot_name:
                warehouse.fleet[bot_name] = AGVRobot(bot_name, 100, RobotStatus.IDLE, "DOCK-NEW")
                warehouse.log(f"Added new AGV '{bot_name}' to fleet.", "SUCCESS")
        elif choice == "6":
            print(f"\n{Colors.OKGREEN}Exiting Smart Warehouse Controller. Goodbye!{Colors.ENDC}")
            break
        else:
            warehouse.log("Invalid menu choice selected.", "WARN")

if __name__ == "__main__":
    main()
