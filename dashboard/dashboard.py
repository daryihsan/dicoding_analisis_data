import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os

sns.set(style='dark')

def create_daily_orders_df(df):
    # Mengelompokkan berdasarkan hari dan menghitung order unik & total harga
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    return daily_orders_df

def create_category_sales_df(df):
    # Menghitung total penjualan per kategori produk
    category_sales_df = df.groupby("product_category_name").order_id.count().reset_index()
    category_sales_df.rename(columns={"order_id": "total_sales"}, inplace=True)
    return category_sales_df

def create_product_sales_df(df):
    # Menghitung total penjualan per produk
    product_sales_df = df.groupby("product_id").order_id.count().reset_index()
    product_sales_df.rename(columns={"order_id": "total_sales"}, inplace=True)
    return product_sales_df

def create_bystate_df(df, entity="customer"):
    # Menghitung jumlah unik pelanggan atau penjual per state
    if entity == "customer":
        bystate_df = df.groupby("customer_state").customer_id.nunique().reset_index()
        bystate_df.rename(columns={"customer_id": "count"}, inplace=True)
    else:
        bystate_df = df.groupby("seller_state").seller_id.nunique().reset_index()
        bystate_df.rename(columns={"seller_id": "count"}, inplace=True)
    
    return bystate_df.sort_values(by="count", ascending=False).head(10)

def create_bycity_df(df, entity="customer"):
    # Menghitung jumlah unik pelanggan atau penjual per city
    if entity == "customer":
        bycity_df = df.groupby("customer_city").customer_id.nunique().reset_index()
        bycity_df.rename(columns={"customer_id": "count"}, inplace=True)
    else:
        bycity_df = df.groupby("seller_city").seller_id.nunique().reset_index()
        bycity_df.rename(columns={"seller_id": "count"}, inplace=True)

    return bycity_df.sort_values(by="count", ascending=False).head(10)

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]
    
    # Hitung recency dinamis berdasarkan filter
    recent_date = df["order_purchase_timestamp"].max().date() + pd.Timedelta(days=1)
    rfm_df["recency"] = rfm_df["max_order_timestamp"].dt.date.apply(lambda x: (recent_date - x).days)
    return rfm_df


# Load data yang sudah diekspor dari notebook
pwd = os.path.dirname(__file__)
main_df = pd.read_csv(os.path.join(pwd, "main_data.csv"))
main_df["order_purchase_timestamp"] = pd.to_datetime(main_df["order_purchase_timestamp"])

# Sidebar untuk filter tanggal
min_date = main_df["order_purchase_timestamp"].min().date()
max_date = main_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    # Menambahkan logo
    st.image("https://png.pngtree.com/png-clipart/20200721/original/pngtree-online-shop-logo-design-vector-png-image_4825109.jpg")
    
    st.write("### Filter Data")
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Pilih Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Filter main_df berdasarkan input tanggal
main_df_filtered = main_df[
    (main_df["order_purchase_timestamp"].dt.date >= start_date) & 
    (main_df["order_purchase_timestamp"].dt.date <= end_date)
]

# Dataframe yang sudah difilter
daily_orders_df = create_daily_orders_df(main_df_filtered)
category_sales_df = create_category_sales_df(main_df_filtered)
product_sales_df = create_product_sales_df(main_df_filtered)
customer_state_df = create_bystate_df(main_df_filtered, entity="customer")
seller_state_df = create_bystate_df(main_df_filtered, entity="seller")
customer_city_df = create_bycity_df(main_df_filtered, entity="customer")
seller_city_df = create_bycity_df(main_df_filtered, entity="seller")
rfm_df = create_rfm_df(main_df_filtered)

# Main dashboard
st.header('🛍️ E-Commerce Dashboard')

# Daily orders overview 
st.subheader('Daily Orders Overview')
col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total Orders", value=f"{total_orders:,}")

with col2:
    # Menggunakan format uang Brazil
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#72BCD4"
)
ax.set_title("Trend Pemesanan Harian", fontsize=20)
ax.tick_params(axis='y', labelsize=15)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

colors_5 = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
colors_10 = ["#72BCD4"] + ["#D3D3D3"] * 9

# Produk dan Kategori Terbaik & Terburuk
st.subheader("Best & Worst Performing Categories")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 8))
top_5_categories = category_sales_df.sort_values(by="total_sales", ascending=False).head(5)
bottom_5_categories = category_sales_df.sort_values(by="total_sales", ascending=True).head(5)

# Chart kiri best performing
sns.barplot(x="total_sales", y="product_category_name", data=top_5_categories, ax=ax[0], palette=colors_5, hue="product_category_name", legend=False)
ax[0].set_title("Best Performing Categories", loc="center", fontsize=20)
ax[0].tick_params(axis='y', labelsize=15)

# Chart kanan worst performing
sns.barplot(x="total_sales", y="product_category_name", data=bottom_5_categories, ax=ax[1], palette=colors_5, hue="product_category_name", legend=False)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Categories", loc="center", fontsize=20)
ax[1].tick_params(axis='y', labelsize=15)

st.pyplot(fig)

st.subheader("Best & Worst Performing Products")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 8))
top_5_products = product_sales_df.sort_values(by="total_sales", ascending=False).head(5)
bottom_5_products = product_sales_df.sort_values(by="total_sales", ascending=True).head(5)

# Chart kiri best performing
sns.barplot(x="total_sales", y="product_id", data=top_5_products, ax=ax[0], palette=colors_5, hue="product_id", legend=False)
ax[0].set_title("Best Performing Products", loc="center", fontsize=20)
ax[0].tick_params(axis='y', labelsize=15)

# Chart kanan worst performing
sns.barplot(x="total_sales", y="product_id", data=bottom_5_products, ax=ax[1], palette=colors_5, hue="product_id", legend=False)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Products", loc="center", fontsize=20)
ax[1].tick_params(axis='y', labelsize=15)

st.pyplot(fig)

# Demografi state & city
st.subheader("Demographics by State")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 8))

# Chart kiri customers
sns.barplot(x="count", y="customer_state", data=customer_state_df, ax=ax[0], palette=colors_10, hue="customer_state", legend=False)
ax[0].set_title("Demography State of Customers", loc="center", fontsize=20)
ax[0].tick_params(axis='y', labelsize=15)

# Chart kanan sellers
sns.barplot(x="count", y="seller_state", data=seller_state_df, ax=ax[1], palette=colors_10, hue="seller_state", legend=False)
ax[1].set_title("Demography State of Sellers", loc="center", fontsize=20)
ax[1].tick_params(axis='y', labelsize=15)

st.pyplot(fig)

st.subheader("Demographics by City")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 8))

# Chart kiri customers
sns.barplot(x="count", y="customer_city", data=customer_city_df, ax=ax[0], palette=colors_10, hue="customer_city", legend=False)
ax[0].set_title("Demography City of Customers", loc="center", fontsize=20)
ax[0].tick_params(axis='y', labelsize=15)

# Chart kanan sellers
sns.barplot(x="count", y="seller_city", data=seller_city_df, ax=ax[1], palette=colors_10, hue="seller_city", legend=False)
ax[1].set_title("Demography City of Sellers", loc="center", fontsize=20)
ax[1].tick_params(axis='y', labelsize=15)

plt.tight_layout()
st.pyplot(fig)

# RFM Analysis
st.subheader("Best Customers Based on RFM Parameters (customer_unique_id)")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Average Recency (days)", value=round(rfm_df.recency.mean(), 1))
with col2:
    st.metric("Average Frequency", value=round(rfm_df.frequency.mean(), 2))
with col3:
    st.metric("Average Monetary", value=format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR'))

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 10))

sns.barplot(y="recency", x="customer_unique_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors_5, ax=ax[0], hue="customer_unique_id", legend=False)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis='x', labelsize=10, rotation=45)

sns.barplot(y="frequency", x="customer_unique_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors_5, ax=ax[1], hue="customer_unique_id", legend=False)
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis='x', labelsize=10, rotation=45)

sns.barplot(y="monetary", x="customer_unique_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors_5, ax=ax[2], hue="customer_unique_id", legend=False)
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis='x', labelsize=10, rotation=45)

st.pyplot(fig)

st.caption('Dicoding Final Project - Dary Ihsan Amanullah')