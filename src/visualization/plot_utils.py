# src/visualization/plot_utils.py

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# --- Fungsi Utilitas Dasar ---
def _setup_plot(title: str = None, xlabel: str = None, ylabel: str = None, figsize: tuple = (10, 6), rotation: int = 0):
    """Pengaturan dasar untuk plot (judul, label, ukuran)."""
    plt.figure(figsize=figsize)
    if title:
        plt.title(title, fontsize=15)
    if xlabel:
        plt.xlabel(xlabel, fontsize=12)
    if ylabel:
        plt.ylabel(ylabel, fontsize=12)
    if rotation:
        plt.xticks(rotation=rotation, ha="right")

def _annotate_bars(ax, percentage: bool = False, total_count: int = None):
    """Memberikan anotasi pada bar plot (jumlah atau persentase)."""
    for p in ax.patches:
        height = p.get_height()
        if pd.isnull(height) or height == 0: # Jangan anotasi bar kosong atau NaN
            continue
        
        value_to_display = height
        if percentage and total_count:
            value_to_display_text = f'{100 * height / total_count:.1f}%'
        elif percentage: # Persentase dari tinggi bar itu sendiri (misal untuk stacked bar 100%)
             value_to_display_text = f'{height:.1f}%'
        else:
            value_to_display_text = f'{int(height)}'
        
        ax.text(p.get_x() + p.get_width() / 2.,
                height + (ax.get_ylim()[1] * 0.01), # Sedikit offset di atas bar
                value_to_display_text,
                ha="center", va="bottom", fontsize=10)

# --- Plot Distribusi Variabel Tunggal (Univariate) ---

def plot_target_distribution(df: pd.DataFrame, target_column: str, figsize: tuple = (8, 6), palette="viridis", show_percentage: bool = True):
    """
    Membuat bar plot untuk distribusi variabel target (kelas) dengan jumlah dan persentase.
    """
    _setup_plot(title=f"Distribusi Variabel Target: {target_column}",
                xlabel=target_column,
                ylabel="Jumlah",
                figsize=figsize)
    ax = sns.countplot(x=target_column, data=df, palette=palette, order=df[target_column].value_counts().index)
    total_count = len(df[target_column])
    _annotate_bars(ax, percentage=show_percentage, total_count=total_count)
    plt.tight_layout()
    plt.show()

def plot_numerical_distribution(df: pd.DataFrame, num_column: str, bins: int = 30, figsize: tuple = (10, 6), color="skyblue", show_kde: bool = True):
    """
    Membuat histogram dan KDE (opsional) untuk distribusi fitur numerik.
    """
    _setup_plot(title=f"Distribusi Fitur Numerik: {num_column}",
                xlabel=num_column,
                ylabel="Frekuensi",
                figsize=figsize)
    sns.histplot(data=df, x=num_column, kde=show_kde, bins=bins, color=color)
    plt.tight_layout()
    plt.show()

def plot_boxplot_single(df: pd.DataFrame, num_column: str, figsize: tuple = (8, 5), color="skyblue", orient: str = 'h'):
    """
    Membuat box plot untuk satu fitur numerik.
    Orientasi bisa 'v' (vertikal) atau 'h' (horizontal).
    """
    if orient == 'h':
        _setup_plot(title=f"Box Plot Fitur: {num_column}", xlabel=num_column, figsize=figsize)
        sns.boxplot(x=df[num_column], color=color, orient='h')
    else: # orient == 'v'
        _setup_plot(title=f"Box Plot Fitur: {num_column}", ylabel=num_column, figsize=figsize)
        sns.boxplot(y=df[num_column], color=color, orient='v')
    plt.tight_layout()
    plt.show()

def plot_categorical_distribution(df: pd.DataFrame, cat_column: str, figsize: tuple = (12, 7), palette="viridis", top_n: int = None, show_percentage: bool = True):
    """
    Membuat count plot untuk distribusi fitur kategorikal dengan jumlah dan persentase.
    top_n: Menampilkan N kategori teratas jika diisi.
    """
    _setup_plot(title=f"Distribusi Fitur Kategorikal: {cat_column}",
                xlabel=cat_column,
                ylabel="Jumlah",
                figsize=figsize,
                rotation=45)

    order = df[cat_column].value_counts()
    if top_n:
        order = order.nlargest(top_n).index
        data_to_plot = df[df[cat_column].isin(order)]
    else:
        order = order.index
        data_to_plot = df

    ax = sns.countplot(x=cat_column, data=data_to_plot, palette=palette, order=order)
    total_count_for_plot = len(data_to_plot[cat_column])
    _annotate_bars(ax, percentage=show_percentage, total_count=total_count_for_plot)
    plt.tight_layout()
    plt.show()

def plot_pie_chart(df: pd.DataFrame, cat_column: str, figsize: tuple = (8, 8), top_n: int = None, explode_largest: bool = True):
    """
    Membuat pie chart untuk distribusi fitur kategorikal.
    Gunakan dengan hati-hati, tidak ideal untuk banyak kategori.
    top_n: Menggabungkan kategori lain menjadi 'Others' jika jumlah kategori > top_n.
    """
    counts = df[cat_column].value_counts()
    labels = counts.index
    sizes = counts.values
    
    if top_n and len(counts) > top_n:
        labels = counts.nlargest(top_n).index.tolist() + ['Others']
        sizes = counts.nlargest(top_n).tolist() + [counts.nsmallest(len(counts) - top_n).sum()]

    explode = None
    if explode_largest and len(labels) > 0:
        explode = [0.05] * len(labels) # Sedikit "ledakan" untuk semua slice
        # Atau hanya untuk yang terbesar:
        # largest_idx = np.argmax(sizes)
        # explode[largest_idx] = 0.1


    _setup_plot(title=f"Pie Chart Fitur: {cat_column}", figsize=figsize)
    plt.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90, pctdistance=0.85)
    plt.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
    centre_circle = plt.Circle((0,0),0.70,fc='white') # Opsional: Donut chart
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    plt.tight_layout()
    plt.show()

# --- Plot Hubungan Antar Variabel (Bivariate/Multivariate) ---

def plot_numerical_vs_categorical_boxplot(df: pd.DataFrame, num_column: str, cat_column: str, figsize: tuple = (12, 7), palette="viridis", orient: str = 'v'):
    """
    Membuat box plot untuk fitur numerik yang dikelompokkan berdasarkan fitur kategorikal.
    """
    if orient == 'v':
        _setup_plot(title=f"Box Plot '{num_column}' vs '{cat_column}'",
                    xlabel=cat_column,
                    ylabel=num_column,
                    figsize=figsize,
                    rotation=45)
        sns.boxplot(x=cat_column, y=num_column, data=df, palette=palette, order=df.groupby(cat_column)[num_column].median().sort_values().index)
    else: # orient == 'h'
        _setup_plot(title=f"Box Plot '{num_column}' vs '{cat_column}'",
                    xlabel=num_column,
                    ylabel=cat_column,
                    figsize=figsize)
        sns.boxplot(x=num_column, y=cat_column, data=df, palette=palette, order=df.groupby(cat_column)[num_column].median().sort_values().index, orient='h')

    plt.tight_layout()
    plt.show()

def plot_numerical_vs_categorical_violinplot(df: pd.DataFrame, num_column: str, cat_column: str, figsize: tuple = (12, 7), palette="viridis", orient: str = 'v'):
    """
    Membuat violin plot untuk fitur numerik yang dikelompokkan berdasarkan fitur kategorikal.
    """
    if orient == 'v':
        _setup_plot(title=f"Violin Plot '{num_column}' vs '{cat_column}'",
                    xlabel=cat_column,
                    ylabel=num_column,
                    figsize=figsize,
                    rotation=45)
        sns.violinplot(x=cat_column, y=num_column, data=df, palette=palette, order=df.groupby(cat_column)[num_column].median().sort_values().index)
    else: # orient == 'h'
        _setup_plot(title=f"Violin Plot '{num_column}' vs '{cat_column}'",
                    xlabel=num_column,
                    ylabel=cat_column,
                    figsize=figsize)
        sns.violinplot(x=num_column, y=cat_column, data=df, palette=palette, order=df.groupby(cat_column)[num_column].median().sort_values().index, orient='h')
    plt.tight_layout()
    plt.show()

def plot_numerical_kde_grouped(df: pd.DataFrame, num_column: str, group_column: str, figsize: tuple = (10,6), palette="viridis"):
    """
    Membuat KDE plot berlapis untuk fitur numerik, dikelompokkan berdasarkan kolom grup (kategorikal).
    """
    _setup_plot(title=f"Distribusi KDE '{num_column}' berdasarkan '{group_column}'",
                xlabel=num_column,
                ylabel="Densitas",
                figsize=figsize)
    sns.kdeplot(data=df, x=num_column, hue=group_column, fill=True, alpha=.5, palette=palette)
    plt.tight_layout()
    plt.show()


def plot_categorical_grouped_countplot(df: pd.DataFrame, cat_column_x: str, cat_column_hue: str, figsize: tuple = (12, 7), palette="viridis", top_n_x: int = None):
    """
    Membuat count plot (grouped bar) untuk dua fitur kategorikal.
    top_n_x: Menampilkan N kategori teratas untuk sumbu x jika diisi.
    """
    _setup_plot(title=f"Distribusi '{cat_column_x}' dikelompokkan berdasarkan '{cat_column_hue}'",
                xlabel=cat_column_x,
                ylabel="Jumlah",
                figsize=figsize,
                rotation=45)

    order_x = df[cat_column_x].value_counts()
    if top_n_x:
        order_x = order_x.nlargest(top_n_x).index
        data_to_plot = df[df[cat_column_x].isin(order_x)]
    else:
        order_x = order_x.index
        data_to_plot = df

    ax = sns.countplot(x=cat_column_x, hue=cat_column_hue, data=data_to_plot, palette=palette, order=order_x)
    _annotate_bars(ax, percentage=False) # Anotasi jumlah, bukan persentase total
    plt.legend(title=cat_column_hue)
    plt.tight_layout()
    plt.show()

def plot_stacked_barplot_percentage(df: pd.DataFrame, cat_col_x: str, cat_col_hue: str, figsize: tuple = (12, 7), palette="viridis", top_n_x: int = None):
    """
    Membuat stacked bar plot 100% untuk dua fitur kategorikal.
    top_n_x: Menampilkan N kategori teratas untuk sumbu x jika diisi.
    """
    _setup_plot(title=f"Distribusi Persentase '{cat_col_hue}' dalam setiap '{cat_col_x}'",
                xlabel=cat_col_x,
                ylabel="Persentase (%)",
                figsize=figsize,
                rotation=45)

    order_x_counts = df[cat_col_x].value_counts()
    if top_n_x:
        order_x = order_x_counts.nlargest(top_n_x).index
        df_filtered = df[df[cat_col_x].isin(order_x)].copy() # Gunakan copy untuk menghindari SettingWithCopyWarning
    else:
        order_x = order_x_counts.index
        df_filtered = df.copy()

    # Hitung persentase
    grouped = df_filtered.groupby(cat_col_x)[cat_col_hue].value_counts(normalize=True).mul(100).rename('percentage').reset_index()
    
    # Pivot untuk plotting dengan Seaborn atau Matplotlib
    pivot_df = grouped.pivot(index=cat_col_x, columns=cat_col_hue, values='percentage').fillna(0)
    
    # Urutkan berdasarkan urutan asli atau top_n
    pivot_df = pivot_df.reindex(order_x)

    pivot_df.plot(kind='bar', stacked=True, figsize=figsize, colormap=palette, ax=plt.gca())
    
    # Anotasi persentase di tengah setiap bagian stack
    ax = plt.gca()
    for c in ax.containers:
        labels = [f'{w:.1f}%' if (w := v.get_height()) > 0 else '' for v in c]
        ax.bar_label(c, labels=labels, label_type='center', fontsize=9, color='white', fontweight='bold')

    plt.legend(title=cat_col_hue, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout to make space for legend
    plt.show()


def plot_scatter(df: pd.DataFrame, x_col: str, y_col: str, hue_col: str = None, size_col: str = None, style_col: str = None, figsize: tuple = (10, 7), palette="viridis", alpha: float = 0.7):
    """
    Membuat scatter plot antara dua fitur numerik, dengan opsi hue, size, dan style.
    """
    _setup_plot(title=f"Scatter Plot: '{y_col}' vs '{x_col}'" + (f" (Hue: {hue_col})" if hue_col else ""),
                xlabel=x_col,
                ylabel=y_col,
                figsize=figsize)
    sns.scatterplot(x=x_col, y=y_col, hue=hue_col, size=size_col, style=style_col, data=df, palette=palette, alpha=alpha, legend="auto")
    if hue_col or size_col or style_col:
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout(rect=[0, 0, 0.85, 1] if hue_col or size_col or style_col else None)
    plt.show()

def plot_correlation_heatmap(df: pd.DataFrame, figsize: tuple = (12, 10), annot: bool = True, cmap="coolwarm"):
    """
    Membuat heatmap korelasi untuk fitur-fitur numerik dalam DataFrame.
    """
    numeric_df = df.select_dtypes(include=np.number)
    if numeric_df.shape[1] < 2:
        print(f"Tidak cukup kolom numerik ({numeric_df.shape[1]}) untuk membuat heatmap korelasi.")
        return

    correlation_matrix = numeric_df.corr()
    _setup_plot(title="Heatmap Korelasi Fitur Numerik", figsize=figsize)
    sns.heatmap(correlation_matrix, annot=annot, cmap=cmap, fmt=".2f", linewidths=.5)
    plt.tight_layout()
    plt.show()

def plot_pairplot(df: pd.DataFrame, columns: list = None, hue_col: str = None, figsize_per_plot: float = 2.5, palette="viridis", corner: bool = False):
    """
    Membuat pair plot (scatterplot matrix) untuk sekumpulan fitur numerik, dengan opsi hue.
    columns: Daftar kolom numerik yang ingin diplot. Jika None, semua kolom numerik akan digunakan.
    figsize_per_plot: Mengontrol ukuran keseluruhan. Ukuran total akan sekitar (jumlah_kolom * figsize_per_plot).
    corner: Jika True, hanya menampilkan bagian bawah matriks (menghindari redundansi).
    """
    if columns:
        data_to_plot = df[columns + ([hue_col] if hue_col and hue_col not in columns else [])]
    else:
        data_to_plot = df.select_dtypes(include=np.number)
        if hue_col and hue_col not in data_to_plot.columns and hue_col in df.columns:
            data_to_plot = pd.concat([data_to_plot, df[[hue_col]]], axis=1)
        elif hue_col and hue_col not in df.columns:
            print(f"Peringatan: Kolom hue '{hue_col}' tidak ditemukan dalam DataFrame.")
            hue_col = None # Abaikan hue jika tidak ada

    if data_to_plot.select_dtypes(include=np.number).shape[1] < 2:
        print(f"Tidak cukup kolom numerik ({data_to_plot.select_dtypes(include=np.number).shape[1]}) untuk pair plot.")
        return

    # Perkirakan ukuran figure
    num_num_cols = data_to_plot.select_dtypes(include=np.number).shape[1]
    fig_size_total = num_num_cols * figsize_per_plot
    
    plt.figure() # Hapus figure default yang mungkin dibuat oleh _setup_plot jika dipanggil
    pair_plot_fig = sns.pairplot(data_to_plot.dropna(subset=data_to_plot.select_dtypes(include=np.number).columns), 
                                 hue=hue_col, 
                                 palette=palette, 
                                 corner=corner, 
                                 height=figsize_per_plot,
                                 diag_kind='kde') # 'hist' atau 'kde'
    pair_plot_fig.fig.suptitle("Pair Plot Fitur Numerik" + (f" (Hue: {hue_col})" if hue_col else ""), y=1.02, fontsize=15)
    plt.tight_layout()
    plt.show()

# --- Plot Spesifik untuk Teks (Contoh Sederhana) ---

def plot_top_n_words_distribution(series: pd.Series, n: int = 20, title: str = "Distribusi Top N Kata", figsize: tuple = (12,8), color="skyblue"):
    """
    Membuat bar plot distribusi frekuensi N kata teratas dari sebuah Series teks.
    Membutuhkan Series yang sudah di-tokenize dan dihitung frekuensinya.
    Contoh penggunaan:
    from collections import Counter
    word_counts = Counter(" ".join(df['url_text_cleaned']).split())
    common_words_series = pd.Series(dict(word_counts.most_common(50)))
    plot_top_n_words_distribution(common_words_series, n=20)
    """
    if not isinstance(series, pd.Series):
        print("Input harus berupa Pandas Series hasil dari penghitungan frekuensi kata.")
        return
        
    top_n_series = series.nlargest(n)
    _setup_plot(title=title, xlabel="Kata", ylabel="Frekuensi", figsize=figsize, rotation=45)
    ax = sns.barplot(x=top_n_series.index, y=top_n_series.values, color=color)
    _annotate_bars(ax)
    plt.tight_layout()
    plt.show()