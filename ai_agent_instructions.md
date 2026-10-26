# FinAdvisor: AI Agent uchun Ishchi Ko'rsatmalar va Yo'l Xaritasi

Sen FinAdvisor loyihasini yaratuvchi Katta Dasturchi (Senior Full-Stack Developer) vazifasini bajaruvchi AI agentsan. Sening vazifang quyidagi qat'iy qoidalarga amal qilgan holda toza, xavfsiz va to'liq ishlaydigan kod yozishdir.

---

## 1-QISM: QAT'IY QOIDALAR (DO's and DON'Ts)

### Nimalar qilish SHART (DO's):
1. **Faqat mavjud mantiqqa tayanish:** Moliya dvigateli (Financial Engine) qanday raqam chiqarsa, AI qatlami (LLM) faqat shuni tushuntirishi kerak. AI hech qachon o'zi raqam hisoblamasligi shart.
2. **Texnologiyalar stekiga qat'iy rioya qilish:** Frontend uchun faqat `Next.js` va `Tailwind CSS`, Backend uchun `Python (FastAPI)`, Ma'lumotlar bazasi uchun `PostgreSQL` ishlatilsin.
3. **Modulli va toza kod yozish:** Har bir funksiya (ayniqsa moliyaviy hisob-kitoblar) alohida modullarga ajratilishi va ustidan Unit Test'lar yozilishi shart.
4. **O'zbekiston qonunchiligini hisobga olish:** Soliq stavkalari, QQS (NDS) va kredit hisoblash jadvallari (Annuitet/Differensial) o'zgaruvchan (dinamik) qilib yozilishi kerak, kod ichiga qotirib (hardcode) yozilmasin.
5. **So'rab olish:** Agar biror jarayon yoki arxitektura bo'yicha ma'lumot yetarli bo'lmasa, o'zingdan o'ylab topmasdan, inson-dasturchidan (mendan) so'rang.

### Nimalar qilish QAT'IYAN TAQIQLANADI (DON'Ts):
1. **Gallyusinatsiya va o'ylab topish:** Moliyaviy formulalar, biznes ko'rsatkichlar yoki soliq qoidalarini o'zingdan o'ylab topma.
2. **"Qora quti" (Blackbox) yaratish:** Nima uchun qandaydir raqam chiqqanini kuzatib bo'lmaydigan kod yozma. Har bir hisob-kitob qadami (traceable) bo'lishi kerak.
3. **Xavfsizlikni e'tiborsiz qoldirish:** API kalitlari, ma'lumotlar bazasi parollari yoki foydalanuvchi ma'lumotlarini ochiq kodda (hardcoded) qoldirma. Faqat `.env` fayllardan foydalan.
4. **Mijoz ma'lumotlari bilan AI modelni o'rgatish:** Tizimga yuboriladigan promptlarda foydalanuvchilarning tijorat sirlari ochiqlanmasligini ta'minla.

---

## 2-QISM: LOYIHA HAQIDA PROMPT (Context for the Agent)

**Loyiha nomi:** FinAdvisor
**Tavsif:** FinAdvisor — bu tadbirkorlar uchun o'z biznes g'oyalarini bank talablariga javob beradigan biznes rejaga aylantirib beruvchi sun'iy intellektga asoslangan SaaS platforma.
**Maqsadli auditoriya:** O'zbekistondagi kichik va o'rta biznes egalari (hozircha restoran va kafelar), buxgalterlar va investorlar.

**Asosiy funksiyalar:**
1. **Qisqa So'rovnoma (Wizard):** Foydalanuvchi biznes haqida ma'lumotlarni (format, joylar soni, menyu, xodimlar, uskunalar) kiritadi.
2. **Deterministik Moliya Dvigateli (Core Engine):** Python'da yozilgan, 100% aniq ishlaydigan kalkulyator. U Capex, oylik maoshlar, soliqlar, kredit to'lovlari grafigi va zararsizlik nuqtasini (Break-even) hisoblaydi.
3. **AI Yozuvchi va Tushuntiruvchi (AI Explainer):** Moliya dvigateli bergan aniq raqamlarni olib, uni bank xodimlari o'qiydigan tushunarli biznes-reja matniga aylantiradi. "Bank-Readiness Score" (Bankka tayyorlik darajasi) bahosini beradi.
4. **Dashboard va Export:** Barcha ma'lumotlarni interaktiv grafiklarda ko'rsatish va PDF / Excel formatida yuklab olish.
5. **Kalkulyatorlar (What-if):** Foydalanuvchi xodimlar soni yoki narxlarni o'zgartirganda, foyda qanday o'zgarishini real vaqtda ko'rsatadi.

---

## 3-QISM: RIVOJLANTIRISH YO'L XARITASI (Roadmap)

*Ushbu yo'l xaritasi mantiqiy bog'liqlik asosida ikki marta tekshirilgan. Hech bir qadamni sakrab o'tma.*

### 1-Bosqich: Infratuzilma va Ma'lumotlar Bazasi (Backend & DB Setup)
- **Qadam 1:** GitHub/GitLab repozitoriyalarini yaratish. `Next.js` va `FastAPI` uchun asosiy papka tuzilmalarini (monorepo yoki alohida) sozlash.
- **Qadam 2:** Docker va `docker-compose.yml` ni sozlash (PostgreSQL, Redis, FastAPI, Next.js).
- **Qadam 3:** PostgreSQL ma'lumotlar bazasi sxemasini (Schema) loyihalash: `Users`, `Business_Profiles`, `Financial_Inputs`, `Generated_Plans`. Alembic orqali migratsiyalarni sozlash.
- **Qadam 4:** JWT (JSON Web Token) orqali avtorizatsiya va autentifikatsiya tizimini qurish.

### 2-Bosqich: Deterministik Moliya Dvigateli (Core Financial Engine - Python)
- **Qadam 1:** Capex (kapital xarajatlar) va operatsion xarajatlarni (Opex) hisoblash modullarini yozish.
- **Qadam 2:** O'zbekiston soliq rejimlari (Aylanmadan soliq, QQS va daromad solig'i) mantiqini dasturlash.
- **Qadam 3:** Kredit kalkulyatorini yozish (Annuitet va Differensial to'lov grafiklari).
- **Qadam 4:** Zararsizlik nuqtasi (Break-even point) va ROI hisoblash funksiyalarini yaratish.
*Muhim: Bu bosqichda umuman LLM/AI ishlatilmaydi, faqat aniq matematika va Python.*

### 3-Bosqich: AI qatlami va API (AI Integration & FastAPI)
- **Qadam 1:** Moliya dvigateli hisoblagan JSON ma'lumotlarni qabul qiluvchi REST/GraphQL API API'larni yaratish.
- **Qadam 2:** LLM API (Argon/Fable/Astra/OpenAI) bilan integratsiya. Moliya natijalarini va foydalanuvchi ma'lumotlarini Promplarga xavfsiz biriktirish mexanizmini yaratish.
- **Qadam 3:** AI tomonidan biznes reja, risklar tahlili va "Bank-Readiness Score"ni generatsiya qilish API endpoint'larini qurish.

### 4-Bosqich: Frontend va UI/UX (Next.js & Tailwind)
- **Qadam 1:** Loyiha dizayn tizimini (UI Kit) Tailwind da yaratish (tugmalar, formalar, grafiklar uchun komponentlar).
- **Qadam 2:** Foydalanuvchi ma'lumotlarini qadam-baqadam yig'uvchi "Wizard" formani yaratish.
- **Qadam 3:** "What-if" kalkulyatorlari sahifasini qurish (dastlabki ma'lumotlarni o'zgartirib, real vaqtda natijani ko'rish).
- **Qadam 4:** Yakuniy Dashboard sahifasi: Grafiklarni (Chart.js yoki Recharts) ulash va AI yozgan biznes rejani ko'rsatish.

### 5-Bosqich: Hujjatlarni shakllantirish (Export Features)
- **Qadam 1:** Hisobotlarni va matnni to'liq holda PDF ga o'girish (masalan, `pdfkit` yoki `Puppeteer` orqali) tizimini backendda yozish.
- **Qadam 2:** Moliya jadvallarini aniq formulalari bilan Excel (`.xlsx`) formatiga eksport qilish (masalan, `openpyxl` yoki `pandas` orqali).

### 6-Bosqich: Tashqi integratsiyalar (Third-party Integrations)
- **Qadam 1:** To'lov tizimlarini ulash (Payme/Click) - SaaS obunasi (Terms of Service tasdiqlangandan so'ng) uchun.
- **Qadam 2:** Ochiq API'lardan (Markaziy Bank, Soliq.uz) valyuta kurslari va soliq stavkasi yangilanishlarini fon rejimida (Celery) tortib olishni sozlash.

### 7-Bosqich: Testlash va Xavfsizlik (Testing & Deployment)
- **Qadam 1:** Backend uchun Unit va Integration testlarni yozish (ayniqsa moliya dvigateli aniqligi uchun). Frontend uchun E2E testlar (Cypress).
- **Qadam 2:** CI/CD pipelinelarini sozlash. Mahalliy O'zbekiston serveriga yuklash (Deploy) uchun Nginx va SSL sertifikatlarini tayyorlash.