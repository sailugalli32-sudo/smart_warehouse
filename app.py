"""
Smart Warehouse Management System - Streamlit Web Dashboard
------------------------------------------------------------
Visual Dashboard for Stock Monitoring, AGV Fleet Controller, Order Allocation & Analytics.
"""

import streamlit as st
import pandas as pd
import random
import time
import sys
import os

# Import core warehouse classes from main.py
from main import SmartWarehouse, RobotStatus, OrderStatus, Item, AGVRobot

# Page Configuration
st.set_page_config(
    page_title="Smart Warehouse & AGV Fleet Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Modern Dark Theme Styling
st.markdown("""
<style>
    /* Metric Cards Styling */
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4A00E0 0%, #8E2DE2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #A0AEC0;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "warehouse" not in st.session_state:
    st.session_state.warehouse = SmartWarehouse("Apex Automated Logistics Hub")

warehouse: SmartWarehouse = st.session_state.warehouse

# Sidebar Navigation & Controls
st.sidebar.title("🤖 Warehouse Control Center")

nav_choice = st.sidebar.radio(
    "Navigate Module",
    ["📊 Dashboard & Operations", "📦 Inventory & Stock", "🤖 AGV Fleet Control", "📋 Order Pipeline", "📈 Analytics & Logs"]
)

st.sidebar.divider()
st.sidebar.subheader("⚡ Quick Actions")

col_s1, col_s2 = st.sidebar.columns(2)
with col_s1:
    if st.sidebar.button("▶️ Step 1 Cycle", use_container_width=True):
        warehouse.tick_simulation()
        st.toast("Simulation advanced by 1 tick!", icon="⚡")
        st.rerun()

with col_s2:
    if st.sidebar.button("🔄 Reset Fleet", use_container_width=True):
        for bot in warehouse.fleet.values():
            bot.battery = 100
            bot.status = RobotStatus.IDLE
            bot.current_location = "DOCK-READY"
        st.toast("AGV fleet reset and fully charged!", icon="🔋")
        st.rerun()

st.sidebar.divider()
auto_play = st.sidebar.toggle("🔄 Auto-Simulate (Loop)", value=False)
if auto_play:
    speed = st.sidebar.slider("Sim Speed (seconds)", 0.5, 3.0, 1.0)
    # Inject order periodically
    if random.random() < 0.5:
        skus = list(warehouse.inventory.keys())
        customers = ["Apple Ops", "SpaceX", "Tesla Giga", "NVIDIA Lab", "Amazon Logistics"]
        warehouse.add_order(random.choice(skus), random.randint(1, 3), random.choice(customers))
    warehouse.tick_simulation()
    time.sleep(speed)
    st.rerun()

# -------------------------------------------------------------
# MODULE 1: MAIN DASHBOARD & OPERATIONS OVERVIEW
# -------------------------------------------------------------
if nav_choice == "📊 Dashboard & Operations":
    st.markdown('<div class="main-header">🤖 Smart Warehouse Control Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-Time Autonomous Fleet Monitoring & Stock Dispatch System</div>', unsafe_allow_html=True)

    # Key Metrics Bar
    m1, m2, m3, m4, m5 = st.columns(5)
    
    avg_bat = sum(r.battery for r in warehouse.fleet.values()) / max(1, len(warehouse.fleet))
    low_stock = sum(1 for item in warehouse.inventory.values() if item.quantity <= item.reorder_level)
    pending_orders = sum(1 for o in warehouse.orders if o.status == OrderStatus.PENDING)

    m1.metric("Total Revenue", f"${warehouse.total_revenue:,.2f}", delta=f"+{warehouse.fulfilled_orders_count} Orders")
    m2.metric("Orders Fulfilled", warehouse.fulfilled_orders_count)
    m3.metric("Pending Orders", pending_orders, delta_color="inverse")
    m4.metric("Avg AGV Battery", f"{avg_bat:.1f}%")
    m5.metric("Low Stock Alerts", low_stock, delta=f"{low_stock} items" if low_stock > 0 else "Optimal", delta_color="inverse")

    st.divider()

    # Main Grid Layout: Left AGV Fleet, Right Inventory Overview
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("🤖 Active AGV Fleet Status")
        fleet_data = []
        for r in warehouse.fleet.values():
            fleet_data.append({
                "Robot ID": r.robot_id,
                "Battery (%)": r.battery,
                "Status": r.status.value,
                "Current Location": r.current_location,
                "Active Task": f"Order {r.current_order_id}" if r.current_order_id else "IDLE"
            })
        df_fleet = pd.DataFrame(fleet_data)
        st.dataframe(
            df_fleet,
            column_config={
                "Battery (%)": st.column_config.ProgressColumn(
                    "Battery (%)",
                    format="%d%%",
                    min_value=0,
                    max_value=100
                ),
            },
            use_container_width=True,
            hide_index=True
        )

    with col_right:
        st.subheader("⚠️ Stock Alert & Quick Reorder")
        low_items = [i for i in warehouse.inventory.values() if i.quantity <= i.reorder_level]
        if low_items:
            for item in low_items:
                st.warning(f"**{item.name} ({item.sku})** - Qty: {item.quantity} (Reorder threshold: {item.reorder_level})")
                if st.button(f"Restock +20 ({item.sku})", key=f"restock_{item.sku}"):
                    warehouse.restock_item(item.sku, 20)
                    st.rerun()
        else:
            st.success("All inventory items are above safety thresholds!")

    st.divider()

    # Recent Activity Log Feed
    st.subheader("📜 Live System Event Stream")
    for log in reversed(warehouse.logs[-6:]):
        st.caption(log)

# -------------------------------------------------------------
# MODULE 2: INVENTORY & STOCK MONITORING
# -------------------------------------------------------------
elif nav_choice == "📦 Inventory & Stock":
    st.title("📦 Inventory Rack & Stock Monitoring")
    st.markdown("Manage rack shelf locations, stock levels, unit pricing, and reorder thresholds.")

    # Inventory Table
    inv_data = []
    for item in warehouse.inventory.values():
        inv_data.append({
            "SKU": item.sku,
            "Name": item.name,
            "Category": item.category,
            "Quantity": item.quantity,
            "Reorder Threshold": item.reorder_level,
            "Shelf Location": item.shelf_location,
            "Unit Price ($)": f"${item.unit_price:.2f}",
            "Stock Status": "⚠️ LOW STOCK" if item.quantity <= item.reorder_level else "✅ NORMAL"
        })
    df_inv = pd.DataFrame(inv_data)
    st.dataframe(df_inv, use_container_width=True, hide_index=True)

    st.divider()
    col_chart, col_add = st.columns([3, 2])

    with col_chart:
        st.subheader("📊 Stock Level vs. Safety Thresholds")
        chart_df = pd.DataFrame({
            "Item": [i.name for i in warehouse.inventory.values()],
            "Current Stock": [i.quantity for i in warehouse.inventory.values()],
            "Reorder Threshold": [i.reorder_level for i in warehouse.inventory.values()]
        }).set_index("Item")
        st.bar_chart(chart_df)

    with col_add:
        st.subheader("➕ Add New Product SKU")
        with st.form("add_sku_form"):
            new_sku = st.text_input("SKU Code", value=f"SKU-{random.randint(200, 999)}")
            new_name = st.text_input("Item Name", value="Industrial Stepper Drive")
            new_cat = st.selectbox("Category", ["Electronics", "Robotics", "Hardware", "Sensors", "Pneumatics"])
            new_qty = st.number_input("Initial Quantity", min_value=1, value=30)
            new_thresh = st.number_input("Reorder Threshold", min_value=1, value=10)
            new_price = st.number_input("Unit Price ($)", min_value=0.0, value=45.00)
            new_loc = st.text_input("Shelf Location", value="D-01")

            if st.form_submit_button("Register Product"):
                warehouse.inventory[new_sku] = Item(new_sku, new_name, new_cat, new_qty, new_thresh, new_price, new_loc)
                warehouse.log(f"Registered new product: {new_name} ({new_sku}) at {new_loc}.", "SUCCESS")
                st.success(f"Product {new_sku} added!")
                st.rerun()

# -------------------------------------------------------------
# MODULE 3: AGV FLEET CONTROL
# -------------------------------------------------------------
elif nav_choice == "🤖 AGV Fleet Control":
    st.title("🤖 Autonomous Guided Vehicle (AGV) Fleet Management")
    st.markdown("Monitor robot battery levels, assign task dispatches, and trigger maintenance.")

    cols = st.columns(len(warehouse.fleet))
    for idx, (bot_id, bot) in enumerate(warehouse.fleet.items()):
        with cols[idx]:
            st.markdown(f"### 🤖 {bot.robot_id}")
            st.metric("Battery Level", f"{bot.battery}%")
            st.progress(bot.battery / 100.0)
            st.write(f"**Status**: `{bot.status.value}`")
            st.write(f"**Location**: `{bot.current_location}`")
            st.write(f"**Task**: `{bot.current_order_id or 'None'}`")

            if st.button(f"Charge ⚡ ({bot.robot_id})", key=f"chg_{bot_id}"):
                bot.status = RobotStatus.CHARGING
                bot.current_location = "CHARGING_BAY"
                st.toast(f"{bot.robot_id} set to charging state.")
                st.rerun()

    st.divider()
    st.subheader("➕ Deploy New AGV Robot")
    col_agv1, col_agv2 = st.columns([2, 1])
    with col_agv1:
        new_agv_name = st.text_input("Robot Identifier", value=f"AGV-Robot-{len(warehouse.fleet)+1}")
    with col_agv2:
        st.write("")
        st.write("")
        if st.button("Deploy AGV to Fleet"):
            warehouse.fleet[new_agv_name] = AGVRobot(new_agv_name, 100, RobotStatus.IDLE, "DOCK-READY")
            warehouse.log(f"Deployed new AGV {new_agv_name} into fleet.", "SUCCESS")
            st.success(f"Deployed {new_agv_name}!")
            st.rerun()

# -------------------------------------------------------------
# MODULE 4: ORDER PIPELINE
# -------------------------------------------------------------
elif nav_choice == "📋 Order Pipeline":
    st.title("📋 Order Allocation & Dispatch Pipeline")
    
    col_order_form, col_order_list = st.columns([1, 2])

    with col_order_form:
        st.subheader("🛒 Place New Order")
        with st.form("place_order_form"):
            selected_sku = st.selectbox("Select SKU", options=list(warehouse.inventory.keys()), format_func=lambda x: f"{x} - {warehouse.inventory[x].name}")
            order_qty = st.number_input("Quantity", min_value=1, value=2)
            cust_name = st.text_input("Customer / Destination", value="Boeing Aerospace")

            if st.form_submit_button("Submit & Dispatch Order"):
                order = warehouse.add_order(selected_sku, order_qty, cust_name)
                if order:
                    warehouse.dispatch_agv()
                    st.success(f"Order {order.order_id} queued successfully!")
                    st.rerun()

    with col_order_list:
        st.subheader("📑 Order History & Live Dispatch Queue")
        if warehouse.orders:
            orders_data = []
            for o in reversed(warehouse.orders):
                item = warehouse.inventory.get(o.sku)
                orders_data.append({
                    "Order ID": o.order_id,
                    "Customer": o.customer_name,
                    "SKU": o.sku,
                    "Item": item.name if item else o.sku,
                    "Quantity": o.quantity,
                    "Total Value": f"${(item.unit_price * o.quantity):,.2f}" if item else "$0.00",
                    "Status": o.status.value,
                    "Assigned AGV": o.assigned_robot_id or "Unassigned"
                })
            st.dataframe(pd.DataFrame(orders_data), use_container_width=True, hide_index=True)
        else:
            st.info("No orders placed yet.")

# -------------------------------------------------------------
# MODULE 5: ANALYTICS & LOGS
# -------------------------------------------------------------
elif nav_choice == "📈 Analytics & Logs":
    st.title("📈 Warehouse Analytics & System Activity")

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.subheader("💰 Revenue by Item Category")
        cat_rev = {}
        for o in warehouse.orders:
            if o.status == OrderStatus.FULFILLED and o.sku in warehouse.inventory:
                item = warehouse.inventory[o.sku]
                cat_rev[item.category] = cat_rev.get(item.category, 0.0) + (item.unit_price * o.quantity)
        
        if cat_rev:
            df_cat = pd.DataFrame(list(cat_rev.items()), columns=["Category", "Revenue ($)"]).set_index("Category")
            st.bar_chart(df_cat)
        else:
            st.info("Fulfill orders to see category revenue analytics.")

    with col_a2:
        st.subheader("🤖 AGV Fleet Battery Levels")
        df_bat = pd.DataFrame({
            "AGV": [r.robot_id for r in warehouse.fleet.values()],
            "Battery %": [r.battery for r in warehouse.fleet.values()]
        }).set_index("AGV")
        st.bar_chart(df_bat)

    st.divider()
    st.subheader("📜 Complete Event Stream Log")
    for log in reversed(warehouse.logs):
        st.text(log)
