import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import string

# Inisialisasi stemmer
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# Fungsi preprocessing teks
def preprocessing(text):
    text = text.lower()                                # Case folding
    text = text.translate(str.maketrans('', '', string.punctuation))  # Hilangkan tanda baca
    text = stemmer.stem(text)                          # Stemming bahasa Indonesia
    return text

# Fungsi utama sistem rekomendasi
def rekomendasi_dosen(topik_mahasiswa):
    # Baca data dosen dari CSV
    df = pd.read_csv('data/dosen.csv')

    # Preprocessing topik dosen
    df['topik_riset'] = df['topik_riset'].apply(preprocessing)

    # Preprocessing input mahasiswa
    topik_mahasiswa = preprocessing(topik_mahasiswa)

    # Gabungkan semua topik dosen + 1 topik mahasiswa
    corpus = df['topik_riset'].tolist()
    corpus.append(topik_mahasiswa)

    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Hitung cosine similarity antara topik mahasiswa dan semua dosen
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

    # Masukkan skor ke dataframe
    df['skor'] = cosine_sim[0]

    # Urutkan berdasarkan skor tertinggi
    hasil = df.sort_values(by='skor', ascending=False).head(3)

    # Ambil kolom yang ingin ditampilkan
    return hasil[['nama', 'bidang', 'topik_riset', 'skor']].to_dict(orient='records')
