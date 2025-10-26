#  KuLatih

Halo! 👋 Selamat datang di repository **Kelompok F03 PBP**.  
Di sini kami mengembangkan project web app **KuLatih** sebagai bagian dari mata kuliah **Pemrograman Berbasis Platform (PBP)**.

---

## 👨‍👩‍👧‍👦 Anggota Kelompok
| No | Nama                          | NPM        |
|----|-------------------------------|------------|
| 1  | Muhammad Salman Fahri          | 2406343514 |
| 2  | Julius Albert Wirayuda         | 2406425792 |
| 3  | Azizah Khairinniswah           | 2406438504 |
| 4  | Khalisha Roselani Prabowo      | 2406496183 |
| 5  | Izzati Maharani Yusmananda     | 2406361675 |
| 6  | Alia Artanti                   | 2406439425 |

---

## 📂 Struktur Project

<details align="justify">
    <summary><b>📖 Deskripsi Aplikasi</b></summary>

## 🏆 KuLatih 🏆
KuLatih adalah sebuah platform berbasis website yang kami kembangkan dengan tujuan utama memberikan ruang eksposur bagi para pelatih di bidang olahraga. Selama ini, banyak pelatih yang memiliki kemampuan dan pengalaman luar biasa, tetapi kesulitan menjangkau calon murid atau komunitas yang membutuhkan jasa mereka. Melalui KuLatih, kami menghadirkan sebuah ekosistem yang tidak hanya menampilkan profil para pelatih secara profesional, tetapi juga memungkinkan mereka untuk lebih mudah ditemukan, dihubungi, dan di-booking oleh pengguna yang sedang mencari pelatih sesuai cabang olahraganya.

Visi kami adalah menjadikan KuLatih sebagai jembatan yang mempertemukan pelatih dengan individu maupun kelompok yang membutuhkan bimbingan, sekaligus menciptakan sebuah komunitas aktif yang saling mendukung dalam proses belajar dan mengajar. Website ini ditujukan bagi dua kelompok utama: para pelatih yang ingin menawarkan jasanya secara lebih luas, serta masyarakat umum yang membutuhkan akses mudah dan terpercaya untuk menemukan pelatih di cabang olahraga spesifik. Dengan adanya fitur booking langsung, integrasi kontak, serta forum komunitas, kami ingin memberikan pengalaman yang lebih dari sekadar marketplace, tetapi juga wadah kolaborasi dan pertukaran ilmu.

Masalah yang kami coba selesaikan adalah keterbatasan platform khusus bagi para pelatih. Saat ini, sebagian besar pelatih hanya mengandalkan promosi dari mulut ke mulut atau media sosial yang sifatnya tersebar dan kurang terorganisir, sehingga peluang mereka untuk mendapatkan murid baru sangat terbatas. Di sisi lain, banyak calon murid kesulitan menemukan pelatih yang tepat karena tidak adanya basis data yang terstruktur. KuLatih hadir untuk mengisi kekosongan ini: kami memberikan solusi berupa platform terpusat yang menyatukan pelatih dan murid dalam satu tempat, memperkuat jaringan komunitas, serta meningkatkan visibilitas para pelatih sehingga mereka dapat berkembang dan mendapatkan apresiasi yang layak atas keahliannya.

</details>

<details align="justify">
    <summary><b>📑 Daftar Modul</b></summary>

1.👤 User Profile
Modul User Profile berfungsi sebagai pusat identitas seluruh pengguna di dalam platform KuLatih, mencakup Coach dan Member. Melalui modul ini, pengguna dapat melihat dan mengelola data pribadi seperti nama, foto profil, informasi kontak, serta riwayat aktivitas dan sesi latihan. Modul ini juga menjadi akses utama untuk mengatur preferensi akun, notifikasi, dan privasi pengguna.

    Fitur utama:
    - Melihat dan mengedit profil pribadi (untuk Member & Coach)
    - Mengganti foto profil
    - Mengelola pengaturan akun & notifikasi
    - Meninjau riwayat booking dan aktivitas latihan
    - Menampilkan perbedaan tampilan dan fitur sesuai peran (Coach atau Member)

2.🏆 Tournament
Modul Tournament menyediakan wadah bagi komunitas olahraga di KuLatih untuk membuat, mengelola, dan berpartisipasi dalam turnamen. Melalui modul ini, pengguna dapat melihat daftar turnamen yang sedang berlangsung maupun yang akan datang, mendaftar sebagai peserta, serta memantau hasil pertandingan. Pelatih juga dapat membuat turnamen untuk cabang olahraga tertentu dan mengatur detail seperti jadwal, peserta, serta sistem pertandingan.

    Fitur utama:
    - Melihat daftar turnamen (All Tournaments & My Tournaments)
    - Membuat dan mengelola turnamen (khusus Coach)
    - Mendaftar dan mengikuti turnamen (untuk Member)
    - Menampilkan detail turnamen seperti jadwal, peserta, dan hasil pertandingan
    - Filter turnamen berdasarkan kategori, cabang olahraga, atau status (ongoing/upcoming)

3. 🗓️ Booking & Jadwal
Modul Booking & Jadwal menjadi inti dari proses interaksi antara pengguna dan pelatih.
Sistem ini memungkinkan pengguna melakukan pemesanan sesi latihan dengan mudah berdasarkan jadwal yang tersedia, serta membantu pelatih dalam mengelola agenda latihannya.
Tujuannya adalah menciptakan proses pemesanan yang efisien, transparan, dan bebas bentrok jadwal.

    Fitur utama:
    - Pemesanan sesi latihan langsung dari profil coach
    - Tampilan kalender jadwal pelatih & pengguna
    - Notifikasi dan pengingat sesi latihan
    - Pembatalan dan penjadwalan ulang secara fleksibel

4. ⭐ Review & Rating
Modul Review & Rating berfungsi sebagai sistem umpan balik untuk menjaga kualitas layanan pelatih.
Setelah sesi latihan selesai, pengguna dapat memberikan penilaian berupa bintang dan ulasan singkat terhadap pelatih maupun pengalaman latihannya.
Sistem ini juga membantu calon pengguna lain dalam memilih pelatih yang terpercaya dan berkualitas.

    Fitur utama:
    - Memberikan rating & ulasan setelah sesi latihan
    - Melihat review pengguna lain
    - Sistem rata-rata rating pelatih
    - Moderasi dan pelaporan ulasan yang tidak sesuai

5. 👥 Community
Modul Community menjadi ruang sosial bagi pengguna KuLatih untuk saling berbagi pengalaman, tips, dan motivasi seputar dunia olahraga.
Di sini, pengguna bisa memposting konten, berdiskusi, serta berinteraksi dengan pelatih maupun anggota komunitas lainnya.
Modul ini mendukung terbentuknya jaringan yang aktif dan inspiratif di antara para pengguna.

    Fitur utama:
    - Feed posting dan update komunitas
    - Like, komentar, dan berbagi postingan
    - Pembuatan grup komunitas olahraga
    - Pengumuman atau event komunitas

6. 💬 Forum
Modul Forum menyediakan wadah diskusi terstruktur untuk topik-topik tertentu.
Berbeda dengan Community yang bersifat sosial dan bebas, Forum difokuskan untuk tanya jawab, berbagi pengetahuan, dan diskusi mendalam antar pengguna dan pelatih.
Dengan adanya Forum, KuLatih menjadi lebih dari sekadar platform booking — tapi juga pusat edukasi dan interaksi.

    Fitur utama:
    - Membuat dan membalas thread diskusi
    - Kategori/topik forum berdasarkan cabang olahraga
    - Fitur pencarian dan filter thread
    - Penandaan jawaban terbaik atau paling membantu
</details>

<details align="justify">
    <summary><b>📊 Initial Data Set</b></summary>
Data set ini bersumber utama dari https://www.superprof.co.id/, dengan beberapa variabel tambahan yang dihasilkan melalui ChatGPT.
</details>

<details align="justify">
    <summary><b>👥 Deskripsi Peran Pengguna</b></summary>

1. 🧑‍🏫 Pelatih (Coach)
Pelatih merupakan pengguna yang menawarkan jasa bimbingan dalam berbagai bidang seperti olahraga dan keterampilan. Mereka berperan sebagai penyedia layanan utama yang dapat menampilkan profil profesional, mengatur jadwal latihan, serta berinteraksi dengan pengguna yang melakukan booking.

    Fitur utama:
    - Membuat dan mengelola profil pelatih
    - Menentukan jadwal ketersediaan latihan
    - Menerima dan mengonfirmasi booking dari pengguna
    - Melihat dan meninjau ulasan dari murid

2. 👤 Pengguna (Murid)
Pengguna adalah individu yang mencari pelatih sesuai kebutuhan mereka. Mereka dapat menelusuri daftar pelatih, melakukan booking sesi latihan, serta memberikan ulasan setelah pelatihan selesai. Peran pengguna menjadi kunci dalam menjaga interaksi dan kualitas layanan di platform.

    Fitur utama:
    - Menelusuri dan memfilter daftar pelatih
    - Melakukan booking dan mengatur jadwal latihan
    - Memberikan rating & ulasan terhadap pelatih
    - Berpartisipasi dalam forum dan komunitas

3. 🛠️ Admin
Admin bertugas sebagai pengelola utama platform KuLatih. Mereka memastikan seluruh fitur berjalan dengan baik, memverifikasi data pelatih, serta menjaga keamanan dan kenyamanan pengguna.

    Fitur utama:
    - Memverifikasi akun pelatih dan pengguna
    - Mengelola data dan laporan aktivitas sistem
    - Memantau forum dan komunitas agar tetap kondusif
    - Menangani pelanggaran, keluhan, dan perbaikan sistem
</details>
    


<details align="justify">
    <summary><b>🌐 Link Deployment</b></summary>
https://muhammad-salman42-kulatih.pbp.cs.ui.ac.id/
</details>

<details align="justify">
    <summary><b>🎨 Link Design</b></summary>
https://www.figma.com/design/0uR1wVLqtNDkJXa9DYLdEF/KuLatih?node-id=0-1&p=f&t=ltEQ5AxvHZHnM78s-0
</details>
