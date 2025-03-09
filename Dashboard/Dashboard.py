import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Dashboard E-commerce", page_icon="📊", layout="wide")

@st.cache_data
def load_data():
    data_path = os.path.join(os.path.dirname(__file__), "Dashboard/all_df.csv.gz")
    df = pd.read_csv(data_path, parse_dates=[
        'order_purchase_timestamp', 
        'order_delivered_customer_date', 
        'order_estimated_delivery_date'
    ])
    return df

all_df = load_data()

st.title("📊 Dashboard E-commerce")
st.markdown("---")

total_revenue = all_df['payment_value'].sum()
total_orders = all_df.shape[0]
total_customers = all_df['customer_unique_id'].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
col2.metric("📦 Total Orders", f"{total_orders:,}")
col3.metric("👥 Total Customers", f"{total_customers:,}")

st.markdown("---")

st.sidebar.header("📅 Filter Rentang Waktu")
start_date = st.sidebar.date_input("Mulai", all_df["order_purchase_timestamp"].min())
end_date = st.sidebar.date_input("Selesai", all_df["order_purchase_timestamp"].max())

all_df = all_df[
    (all_df["order_purchase_timestamp"] >= pd.to_datetime(start_date)) &
    (all_df["order_purchase_timestamp"] <= pd.to_datetime(end_date))
]

st.subheader("🏙️ Kota Asal Seller Terbanyak")
if 'seller_city' in all_df.columns:
    seller_counts = all_df['seller_city'].value_counts().head(10)
    fig = px.bar(seller_counts, x=seller_counts.index, y=seller_counts.values, 
                 labels={'x': 'Kota', 'y': 'Jumlah Seller'}, title="Top 10 Kota Seller")
    st.plotly_chart(fig, use_container_width=True)
    st.write("🔹 **Kota dengan seller terbanyak menunjukkan area dengan aktivitas e-commerce tertinggi.**")
else:
    st.warning("Data kota seller tidak tersedia.")

st.subheader("📈 Tren Jumlah Pesanan 6 Bulan Terakhir")
all_df['month_year'] = all_df['order_purchase_timestamp'].dt.to_period('M')
order_trend = all_df.groupby('month_year').size().tail(6)
fig = px.line(order_trend, x=order_trend.index.astype(str), y=order_trend.values, markers=True, 
              labels={'x': 'Bulan', 'y': 'Jumlah Pesanan'}, title="Tren Pesanan")
st.plotly_chart(fig, use_container_width=True)
st.write("📊 **Tren ini membantu memahami pola belanja pelanggan dalam 6 bulan terakhir.**")

st.subheader("💎 Analisis Pelanggan Loyal")
all_df['recency'] = (all_df['order_purchase_timestamp'].max() - all_df['order_purchase_timestamp']).dt.days
df_rfm = all_df.groupby('customer_unique_id').agg({
    'recency': 'min',
    'customer_unique_id': 'count',
    'payment_value': 'sum'
}).rename(columns={'customer_unique_id': 'frequency', 'payment_value': 'monetary'})

def rfm_segmentation(df):
    df['R_Score'] = pd.qcut(df['recency'], 4, labels=[4, 3, 2, 1], duplicates='drop')
    df['F_Score'] = pd.qcut(df['frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
    df['M_Score'] = pd.qcut(df['monetary'].rank(method='first'), 4, labels=[1, 2, 3, 4])
    df['RFM_Score'] = df[['R_Score', 'F_Score', 'M_Score']].sum(axis=1)
    return df

df_rfm = rfm_segmentation(df_rfm)
st.dataframe(df_rfm.sort_values(by='RFM_Score', ascending=False).head(10))
st.write("👥 **Analisis ini membantu mengidentifikasi pelanggan paling berharga berdasarkan kebiasaan belanja mereka.**")

st.subheader("⭐ Distribusi Rating Pelanggan")
if 'review_score' in all_df.columns:
    fig = px.histogram(all_df, x='review_score', nbins=5, title="Distribusi Skor Review Pelanggan", 
                       labels={'review_score': 'Rating'})
    st.plotly_chart(fig, use_container_width=True)
    st.write("⭐ **Sebaran skor review pelanggan menunjukkan tingkat kepuasan pelanggan secara keseluruhan.**")
else:
    st.warning("Data rating pelanggan tidak tersedia.")

st.subheader("⏳ Kontrol Keterlambatan Pengiriman")
if 'order_delivered_customer_date' in all_df.columns:
    all_df['delay_days'] = (all_df['order_delivered_customer_date'] - all_df['order_estimated_delivery_date']).dt.days
    fig = px.histogram(all_df, x='delay_days', nbins=30, title="Sebaran Keterlambatan Pengiriman", 
                       labels={'delay_days': 'Hari Keterlambatan'})
    st.plotly_chart(fig, use_container_width=True)
    st.write("📦 **Grafik ini membantu dalam mengontrol performa logistik berdasarkan keterlambatan pengiriman.**")
else:
    st.warning("Data keterlambatan pengiriman tidak tersedia.")

st.subheader("📦 Perbandingan Estimasi vs Realisasi Pengiriman")
if 'delay_days' in all_df.columns:
    all_df['delivery_status'] = all_df['delay_days'].apply(lambda x: 'Lebih Cepat' if x < 0 else ('Tepat Waktu' if x == 0 else 'Terlambat'))
    delivery_counts = all_df['delivery_status'].value_counts()
    fig = px.bar(delivery_counts, x=delivery_counts.index, y=delivery_counts.values, title="Status Pengiriman")
    st.plotly_chart(fig, use_container_width=True)
    st.write("📌 **Analisis ini menunjukkan seberapa sering pesanan datang tepat waktu, lebih cepat, atau terlambat.**")
else:
    st.warning("Data keterlambatan tidak tersedia.")

st.subheader("🏆 Kategori Produk Paling Laris")
if 'product_category_name' in all_df.columns:
    product_counts = all_df['product_category_name'].value_counts().head(10)
    fig = px.bar(x=product_counts.index, y=product_counts.values, 
                 labels={'x': 'Kategori Produk', 'y': 'Jumlah Pesanan'}, title="Top 10 Kategori Produk")
    st.plotly_chart(fig, use_container_width=True)
    
    top_category = all_df['product_category_name'].value_counts().idxmax()
    st.write(f"🎯 **Kategori Produk Paling Laris:** `{top_category}`")
    df_top_category = all_df[all_df['product_category_name'] == top_category]
    category_trend = df_top_category.groupby(df_top_category['order_purchase_timestamp'].dt.to_period('M')).size()
    fig2 = px.line(x=category_trend.index.astype(str), y=category_trend.values, markers=True, 
                   labels={'x': 'Bulan', 'y': 'Jumlah Pesanan'}, title=f"Tren Penjualan Kategori {top_category}")
    st.plotly_chart(fig2, use_container_width=True)
    st.write("📊 **Analisis tren penjualan untuk kategori produk paling laris.**")
else:
    st.warning("Data kategori produk tidak tersedia.")

st.subheader("📆 Distribusi Pesanan Berdasarkan Hari")
all_df['order_day'] = all_df['order_purchase_timestamp'].dt.day_name()
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
order_day_counts = all_df['order_day'].value_counts().reindex(days_order)
fig = px.bar(x=order_day_counts.index, y=order_day_counts.values, 
             labels={'x': 'Hari', 'y': 'Jumlah Pesanan'}, title="Distribusi Pesanan per Hari")
st.plotly_chart(fig, use_container_width=True)
st.write("📅 **Grafik ini menunjukkan jumlah pesanan yang diterima di setiap hari dalam seminggu.**")

st.subheader("🔍 Korelasi Keterlambatan Pengiriman vs. Rating")
if 'delay_days' in all_df.columns and 'review_score' in all_df.columns:
    fig = px.scatter(all_df, x='delay_days', y='review_score', title="Korelasi Keterlambatan vs. Rating", 
                     labels={'delay_days': 'Hari Keterlambatan', 'review_score': 'Rating'}, trendline="ols")
    st.plotly_chart(fig, use_container_width=True)
    st.write("🔍 **Analisis ini membantu mengevaluasi apakah terdapat hubungan antara keterlambatan pengiriman dan tingkat kepuasan pelanggan.**")
else:
    st.warning("Data keterlambatan atau rating tidak tersedia.")
    
st.subheader("💵 Nilai Pesanan Rata-rata (AOV)")
aov = total_revenue / total_orders if total_orders > 0 else 0
st.metric("AOV", f"${aov:,.2f}")
st.write("📌 **AOV menunjukkan rata-rata nilai pesanan per transaksi, berguna untuk mengukur kinerja penjualan.**")

st.subheader("📊 Revenue Berdasarkan Kota Seller")
if 'seller_city' in all_df.columns:
    revenue_by_city = all_df.groupby('seller_city')['payment_value'].sum().sort_values(ascending=False).head(10)
    fig = px.bar(revenue_by_city, x=revenue_by_city.index, y=revenue_by_city.values, 
                 labels={'x': 'Kota Seller', 'y': 'Total Pendapatan'}, title="Top 10 Kota Seller Berdasarkan Pendapatan")
    st.plotly_chart(fig, use_container_width=True)
    st.write("📈 **Grafik ini membantu mengidentifikasi kota dengan potensi penjualan tinggi.**")
else:
    st.warning("Data seller city tidak tersedia.")

st.subheader("🏆 Pelanggan Teratas Berdasarkan Revenue")
top_customers = all_df.groupby('customer_unique_id')['payment_value'].sum().sort_values(ascending=False).head(10)
fig = px.bar(top_customers, x=top_customers.index, y=top_customers.values, 
             labels={'x': 'ID Pelanggan', 'y': 'Total Pendapatan'}, title="Top 10 Pelanggan Berdasarkan Pendapatan")
st.plotly_chart(fig, use_container_width=True)
st.write("👑 **Mengidentifikasi pelanggan dengan pengeluaran tinggi dapat membantu strategi pemasaran yang lebih tepat sasaran.**")

st.subheader("📈 Revenue Bulanan & Tingkat Pertumbuhan")
monthly_revenue = all_df.groupby(all_df['order_purchase_timestamp'].dt.to_period('M'))['payment_value'].sum().sort_index()
monthly_revenue_df = monthly_revenue.to_frame().reset_index()
monthly_revenue_df['bulan_tahun'] = monthly_revenue_df['order_purchase_timestamp'].astype(str)
monthly_revenue_df['tingkat_pertumbuhan'] = monthly_revenue_df['payment_value'].pct_change() * 100
fig = px.bar(monthly_revenue_df, x='bulan_tahun', y='payment_value', 
             title="Pendapatan Bulanan", labels={'payment_value': 'Pendapatan'})
st.plotly_chart(fig, use_container_width=True)
st.write("📊 **Grafik ini memberikan gambaran tren pendapatan bulanan dan pertumbuhan penjualan.**")

st.write("📝 **Sumber Data:** `all_df.csv.gz`")
