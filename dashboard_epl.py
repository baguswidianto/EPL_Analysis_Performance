import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ====================================================================
# Konfigurasi Halaman
# ====================================================================
# Konfigurasi halaman harus menjadi perintah Streamlit pertama yang dijalankan.
st.set_page_config(
    page_title="Dasbor Analisis Pemain EPL",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================================
# Fungsi Pemuatan Data dengan Caching
# ====================================================================
@st.cache_data
def load_data(file_path):
    """
    Memuat data pemain dari file CSV, melakukan pembersihan dasar,
    dan mengoptimalkan kinerja dengan caching.
    """
    try:
        df = pd.read_csv(file_path)
        # Pembersihan data yang lebih kuat: Mengonversi kolom persentase dari string ke float
        for col in df.columns:
            if df[col].dtype == 'object' and df[col].str.contains('%', na=False).any():
                df[col] = df[col].str.replace('%', '', regex=False).astype(float) / 100.0
        return df
    except FileNotFoundError:
        st.error(f"File tidak ditemukan di {file_path}. Pastikan file 'epl_player_stats_24_25.csv' ada di direktori yang sama.")
        return None

# Memuat data
df = load_data('epl_player_stats_24_25.csv')

if df is None:
    st.stop()

# ====================================================================
# Sidebar untuk Filter
# ====================================================================
st.sidebar.header("Panel Filter ⚙️")

# Filter Klub
clubs = sorted(df['Club'].unique())
selected_clubs = st.sidebar.multiselect(
    'Pilih Klub:',
    options=clubs,
    default=['Arsenal', 'Manchester City', 'Liverpool', 'Manchester United']
)

# Filter Posisi
positions = ['All'] + sorted(df['Position'].unique())
selected_position = st.sidebar.selectbox('Pilih Posisi:', positions)

# Filter Menit Bermain
min_minutes, max_minutes = int(df['Minutes'].min()), int(df['Minutes'].max())
selected_minutes_range = st.sidebar.slider(
    'Filter Menit Bermain:',
    min_value=min_minutes,
    max_value=max_minutes,
    value=(min_minutes, max_minutes)
)

# ====================================================================
# Judul Utama Aplikasi
# ====================================================================
st.title("⚽ Dasbor Analisis Pemain Premier League 2024/25")
st.write("Selamat datang di dasbor interaktif untuk menganalisis statistik pemain dari English Premier League. Gunakan panel filter di sebelah kiri untuk menjelajahi data.")

# ====================================================================
# Logika Pemfilteran Data
# ====================================================================
# Mulai dengan salinan DataFrame yang belum difilter
filtered_df = df.copy()

# Terapkan filter berdasarkan klub
if selected_clubs:
    filtered_df = filtered_df[filtered_df['Club'].isin(selected_clubs)]
else:
    # Jika tidak ada klub yang dipilih, tampilkan DataFrame kosong
    filtered_df = pd.DataFrame(columns=df.columns)

# Terapkan filter berdasarkan posisi
if selected_position != 'All':
    filtered_df = filtered_df[filtered_df['Position'] == selected_position]

# Terapkan filter berdasarkan rentang menit bermain
if not filtered_df.empty:
    filtered_df = filtered_df[
        (filtered_df['Minutes'] >= selected_minutes_range[0]) &
        (filtered_df['Minutes'] <= selected_minutes_range[1])
    ]

# ====================================================================
# Tampilan Metrik Kunci (KPI)
# ====================================================================
if not filtered_df.empty:
    total_players = len(filtered_df)
    total_goals = int(filtered_df['Goals'].sum())
    avg_assists = round(filtered_df['Assists'].mean(), 2)
    avg_minutes = round(filtered_df['Minutes'].mean(), 0)
else:
    total_players = 0
    total_goals = 0
    avg_assists = 0
    avg_minutes = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Jumlah Pemain", f"{total_players:,}")
col2.metric("Total Gol", f"{total_goals:,}")
col3.metric("Rata-rata Assist", f"{avg_assists}")
col4.metric("Rata-rata Menit Bermain", f"{int(avg_minutes):,}")

st.divider()

# ====================================================================
# Layout Tab untuk Visualisasi
# ====================================================================
tab1, tab2, tab3 = st.tabs(["Analisis Visual Gabungan", "Peringkat Pemain", "Data Lengkap"])

with tab1:
    st.header("Analisis Visual Gabungan")

    # Peringatan jika tidak ada data
    if filtered_df.empty:
        st.warning("Tidak ada data yang tersedia untuk filter yang dipilih. Silakan sesuaikan filter Anda.")
    else:
        # Grafik 1: Total Gol per Klub
        st.subheader('Total Gol per Klub')
        goals_by_club = filtered_df.groupby('Club')['Goals'].sum().sort_values(ascending=False)
        st.bar_chart(goals_by_club)

        # Grafik 2: Analisis Tembakan vs. Gol (Scatter Plot Interaktif)
        st.subheader('Analisis Tembakan vs. Gol')
        fig_scatter = px.scatter(
            filtered_df,
            x='Shots',
            y='Goals',
            color='Club',
            hover_name='Player Name',
            hover_data=['Position', 'Minutes'],
            title='Korelasi antara Jumlah Tembakan dan Gol'
        )
        fig_scatter.update_layout(
            xaxis_title="Jumlah Tembakan",
            yaxis_title="Jumlah Gol"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.header("Peringkat Pemain Unggulan")

    if filtered_df.empty:
        st.warning("Tidak ada data untuk ditampilkan pada peringkat.")
    else:
        # Pilih metrik yang relevan untuk diperingkatkan
        numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
        # Hapus kolom yang tidak relevan untuk peringkat pemain individu
        metrics_to_exclude = ['Big Chances Missed', 'Hit Woodwork', 'Offsides', 'Goals Conceded', 'Own Goals', 'Yellow Cards', 'Red Cards', 'Penalties Saved']
        metrics_to_rank = [col for col in numeric_cols if col not in metrics_to_exclude and 'Ended' not in col and 'xGoT' not in col]

        metric_selection = st.selectbox(
            'Pilih Metrik untuk Peringkat:',
            options=sorted(metrics_to_rank),
            index=metrics_to_rank.index('Goals') if 'Goals' in metrics_to_rank else 0
        )

        if metric_selection:
            top_10_players = filtered_df.nlargest(10, metric_selection)
            fig_bar_top = px.bar(
                top_10_players.sort_values(metric_selection, ascending=True),
                x=metric_selection,
                y='Player Name',
                orientation='h',
                title=f'Top 10 Pemain Berdasarkan {metric_selection}',
                text=metric_selection,
                color=metric_selection,
                color_continuous_scale=px.colors.sequential.Viridis
            )
            fig_bar_top.update_layout(
                yaxis_title="Nama Pemain",
                xaxis_title=metric_selection,
                yaxis={'categoryorder':'total ascending'}
            )
            st.plotly_chart(fig_bar_top, use_container_width=True)

with tab3:
    st.header("Data Lengkap Pemain (Difilter)")
    st.info("Anda dapat mengurutkan kolom dengan mengklik headernya atau mencari data di dalam tabel.")

    if filtered_df.empty:
        st.warning("Tidak ada data yang cocok dengan filter yang Anda pilih.")
    else:
        st.dataframe(
            filtered_df,
            column_config={
                "Passes%": st.column_config.ProgressColumn(
                    "Akurasi Umpan",
                    help="Persentase umpan yang berhasil.",
                    format="%.2f%%",
                    min_value=0,
                    max_value=1,
                ),
                "Goals": st.column_config.NumberColumn(
                    "Gol ⚽",
                    help="Total gol yang dicetak pemain."
                ),
                "Assists": st.column_config.NumberColumn(
                    "Assist 🎯"
                ),
                "Club": st.column_config.TextColumn(
                    "Klub"
                ),
                "Player Name": st.column_config.TextColumn(
                    "Nama Pemain"
                )
            },
            use_container_width=True,
            hide_index=True
        )
