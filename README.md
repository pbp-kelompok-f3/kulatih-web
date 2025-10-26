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

KuLatih adalah platform website yang dirancang untuk menjembatani pelatih olahraga dengan individu atau kelompok yang membutuhkan bimbingan. Banyak pelatih memiliki kemampuan dan pengalaman luar biasa, tetapi kesulitan menjangkau calon murid karena promosi yang tersebar dan kurang terstruktur. Sementara itu, calon murid sering kesulitan menemukan pelatih yang sesuai dengan cabang olahraga yang diminati.

Melalui KuLatih, pelatih dapat membuat profil profesional, menampilkan keahlian, menerima booking langsung dari murid, dan mengelola turnamen olahraga. Fitur turnamen memungkinkan pelatih:
- Membuat turnamen baru sesuai cabang olahraga yang diajarkan.
- Mengedit informasi turnamen yang telah dibuat.
- Melihat daftar peserta yang mendaftar pada turnamennya.
- Menghapus turnamen bila diperlukan.

Dengan fitur ini, pelatih tidak hanya mengajar, tetapi juga dapat mengadakan kompetisi, membangun komunitas, dan meningkatkan interaksi dengan murid atau peserta.

Bagi masyarakat umum, KuLatih memberikan akses mudah untuk menemukan pelatih, memesan sesi pelatihan, serta mengikuti turnamen yang diadakan oleh pelatih. Forum komunitas memungkinkan pengguna untuk berdiskusi, bertanya, dan berbagi pengalaman secara interaktif.

Kebermanfaatan KuLatih meliputi:
1. Meningkatkan visibilitas pelatih sehingga lebih mudah ditemukan dan dihargai atas keahliannya.
2. Mempermudah calon murid menemukan pelatih dan mengikuti sesi pelatihan atau turnamen secara terstruktur.
3. Membangun komunitas olahraga yang aktif melalui forum dan turnamen.
4. Memberikan pengalaman profesional bagi pelatih dan peserta dalam manajemen kelas maupun kompetisi olahraga.

Dengan demikian, KuLatih hadir sebagai solusi terpadu yang menghubungkan pelatih dan murid, sekaligus menciptakan ekosistem olahraga yang profesional, kolaboratif, dan interaktif melalui fitur turnamen, booking, dan komunitas.
</details>

<details align="justify">
    <summary><b>📑 Daftar Modul</b></summary>

## 🏃 Modul: <i>User Profile</i> (Albert) 🏃

Modul **User Profile** bertanggung jawab untuk manajemen data pengguna dalam platform KuLatih. Modul ini terbagi menjadi dua bagian utama: **Member** dan **Profile**.
Submodul **Member** menangani informasi dasar pengguna yang mendaftar di platform, member sebagai murid. Fitur utamanya meliputi:
- Registrasi dan login pengguna.
- Menyimpan data identitas dasar (nama,foto, email, role, dan informasi kontak).
- Pengaturan akun dasar, termasuk reset password dan status aktif/non-aktif.
- Mengikuti kompetisi yang dibuat oleh Coach

Submodul **Coach** fokus pada pengelolaan informasi profil pelatih secara lebih rinci. Fitur utamanya meliputi:
- Membuat dan mengedit profil profesional pelatih.
- Menampilkan keahlian, pengalaman, dan cabang olahraga yang dikuasai.
- Melihat review dari murid dan rating profil.
- Mengelola foto dan informasi tambahan yang memperkuat reputasi pengguna di platform.
- Membuat sebuah kompetisi yang dapat diikuti oleh Member

## 🏆 Modul: <i>Tournament</i> (Salman) 🏆

Modul **Tournament** bertanggung jawab untuk pengelolaan kompetisi olahraga yang dibuat oleh pelatih di platform KuLatih. Modul ini dirancang agar pelatih dapat mengelola turnamen secara penuh, mulai dari pembuatan hingga pemantauan peserta.

- **Membuat Turnamen**: Pelatih dapat membuat turnamen baru dengan mengatur nama, cabang olahraga, tanggal, lokasi, dan deskripsi turnamen.  
- **Mengedit Turnamen**: Pelatih dapat memperbarui informasi turnamen yang sudah dibuat, termasuk jadwal, aturan, dan detail lainnya.  
- **Melihat Peserta Turnamen**: Pelatih dapat melihat daftar peserta yang mendaftar pada turnamennya, lengkap dengan data kontak dan status pendaftaran.  
- **Menghapus Turnamen**: Pelatih dapat menghapus turnamen jika dibatalkan.  

Modul ini membantu pelatih untuk tidak hanya mengajar, tetapi juga membangun komunitas kompetitif dan interaktif, serta memberikan pengalaman profesional bagi peserta turnamen.

## 🗓️ Modul: <i>Booking</i> (Khalisha) 🗓️

Modul **Booking** berfungsi untuk mengelola pemesanan sesi pelatihan antara murid (member) dan pelatih (coach) di platform KuLatih. Modul ini memastikan proses booking berjalan mudah, terstruktur, dan transparan.

- **Pemesanan Sesi Latihan Langsung melalui Profil Coach**: Member dapat langsung memesan sesi latihan melalui profile pelatih.  
- **Daftar Jadwal Sesi Latihan**: Menampilkan daftar jadwal sesi latihan yang sedang berlangsung maupun yang telah dilakukan.  
- **Notifikasi Otomatis**: Sistem mengirimkan notifikasi otomatis untuk konfirmasi booking, pembatalan, dan pengingat sesi latihan.  
- **Fleksibilitas Reschedule dan Cancel**: Member dan pelatih dapat melakukan reschedule atau cancel sesuai kebutuhan.  
- **Status Booking Otomatis**: Status booking akan berubah menjadi "completed" secara otomatis setelah sesi latihan berakhir.  

Modul ini membantu menciptakan pengalaman profesional, terorganisir, dan fleksibel bagi member dan coach, sehingga interaksi dan transaksi di platform KuLatih menjadi lebih efisien dan terpercaya.

## ⭐ Modul: <i>Reviews</i> (Airin) ⭐

Modul **Reviews** berfungsi untuk mengelola sistem penilaian dan ulasan dari member terhadap pelatih di platform KuLatih. Modul ini membantu membangun reputasi pelatih serta memberikan referensi bagi calon murid lain.

- **Memberikan Rating & Ulasan**: Member dapat memberikan rating dan ulasan setelah sesi latihan melalui form modal interaktif.  
- **Melihat Review di Profil Coach**: Semua review dan rating ditampilkan di halaman profil pelatih untuk meningkatkan transparansi dan kepercayaan.  
- **Filter Review**: Pengguna dapat memfilter review berdasarkan jumlah bintang untuk menemukan ulasan yang relevan.  
- **Edit dan Hapus Review**: Pengguna dapat mengedit atau menghapus review yang telah mereka buat.  

Modul ini membantu pelatih meningkatkan kualitas layanannya melalui umpan balik dari member, sekaligus memberikan informasi yang berguna bagi calon murid dalam memilih pelatih yang tepat.

## 💬 Modul: Forum (Izzati) 💬

Modul **Forum** menyediakan wadah diskusi yang terstruktur untuk berbagai topik tertentu. Berbeda dengan modul **Community** yang bersifat lebih sosial dan bebas, Forum difokuskan pada kegiatan tanya jawab, berbagi pengetahuan, serta diskusi mendalam antara pengguna dan pelatih.

Dengan adanya Forum, KuLatih tidak hanya menjadi platform pemesanan (<i>booking</i>) semata, tetapi juga berkembang menjadi pusat edukasi dan interaksi bagi seluruh pengguna.

- **Membuat dan Membalas Thread Diskusi**: Pengguna dapat membuat topik baru atau membalas thread yang sudah ada.  
- **Pencarian dan Penyaringan Pesan**: Memudahkan pengguna menemukan diskusi atau topik tertentu.  
- **Menghapus dan Mengedit Postingan**: Pengguna dapat mengedit atau menghapus postingan yang mereka buat.  
- **Upvote dan Downvote**: Pengguna dapat memberikan upvote atau downvote pada postingan untuk menilai kualitas konten.  

Modul ini mendukung interaksi yang terstruktur dan membantu pengguna saling berbagi pengetahuan, pengalaman, dan strategi terkait olahraga.

## 👥 Modul: Community (Alia) 👥

Modul **Community** berfungsi sebagai ruang sosial yang lebih bebas bagi pengguna KuLatih untuk berinteraksi, berbagi pengalaman, dan membangun jaringan. Berbeda dengan Forum yang fokus pada diskusi terstruktur, Community bersifat lebih santai dan interaktif.

- **Membuat dan Bergabung dengan Komunitas**: Pengguna dapat membuat komunitas baru sesuai minat atau cabang olahraga, serta bergabung dengan komunitas yang sudah ada.  
- **Posting <i>Chat</i> dan Diskusi Ringan**: Pengguna dapat membagikan pengalaman, tips, atau informasi terkait olahraga dalam bentuk postingan.   
- **Edit dan Hapus <i>Chat/Post</i>**: Pengguna dapat mengedit atau menghapus chat atau postingan yang mereka buat.  
- **Filter Community**: Pengguna dapat memfilter tampilan komunitas antara **All Community** dan **My Community** untuk melihat komunitas yang relevan.    

Modul ini membantu membangun ekosistem sosial yang aktif, memungkinkan pengguna berbagi pengalaman, memperluas jaringan, dan membentuk komunitas olahraga yang suportif dan kolaboratif.
</details>

<details align="justify">
    <summary><b>📊 Initial Data Set</b></summary>
Data set ini bersumber utama dari https://www.superprof.co.id/, dengan beberapa variabel tambahan yang dihasilkan melalui ChatGPT.
</details>

<details align="justify">
    <summary><b>👥 Deskripsi Peran Pengguna</b></summary>

# Peran Pengguna di KuLatih
1. 🧑‍🏫 **Pelatih (<i>Coach</i>)** 🧑‍🏫
Pelatih merupakan pengguna yang menawarkan jasa bimbingan dalam berbagai bidang, khususnya olahraga. Mereka berperan sebagai penyedia layanan utama, dapat menampilkan profil profesional, mengatur jadwal latihan, serta berinteraksi dengan pengguna yang melakukan booking. Pelatih juga dapat membuat dan mengelola turnamen untuk meningkatkan engagement dengan murid dan komunitas.

**Fitur Utama Pelatih:**
- Membuat dan mengelola profil profesional.  
- Menentukan jadwal ketersediaan latihan.  
- Menerima, mengonfirmasi, atau menolak booking dari pengguna.  
- Melihat dan meninjau rating serta ulasan dari murid.  
- Membuat, mengedit, melihat peserta, dan menghapus turnamen.  
- Berinteraksi dengan pengguna melalui forum dan komunitas.

2. 👤 **Pengguna (Murid/<i>Member</i>)**   👤
Pengguna adalah individu yang mencari pelatih sesuai kebutuhan mereka. Mereka dapat menelusuri daftar pelatih, melakukan booking sesi latihan, memberikan ulasan, serta ikut berpartisipasi dalam turnamen dan komunitas. Peran pengguna penting untuk menjaga interaksi dan kualitas layanan di platform.

**Fitur Utama Pengguna:**
- Menelusuri, memfilter, dan mencari pelatih sesuai cabang olahraga dan preferensi.  
- Melakukan booking dan mengatur jadwal sesi latihan.  
- Memberikan rating dan ulasan terhadap pelatih setelah sesi selesai.  
- Berpartisipasi dalam forum dan komunitas untuk berdiskusi atau berbagi pengalaman.  
- Mengikuti dan berpartisipasi dalam turnamen yang diadakan pelatih.
</details>
<details align="justify">
    <summary><b>🌐 Link Deployment</b></summary>
https://muhammad-salman42-kulatih.pbp.cs.ui.ac.id/
</details>

<details align="justify">
    <summary><b>🎨 Link Design</b></summary>
https://www.figma.com/design/0uR1wVLqtNDkJXa9DYLdEF/KuLatih?node-id=0-1&p=f&t=ltEQ5AxvHZHnM78s-0
</details>
