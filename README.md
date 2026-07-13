# Vardiya — planlama ve geri bildirim çalışma alanı

Proje artık iki bağımsız uygulamadan oluşur:

- `frontend/`: Next.js üretim planlama arayüzü ve ortak geri bildirim sayfası
- `backend/`: FastAPI, Clerk oturum doğrulaması, SQLite verisi, görseller ve sesli notlar

Excel kaynak dosyası proje kökünde salt okunur kaynak olarak tutulur.

## Yerel çalıştırma

İlk terminal:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8000 --env-file .env
```

İkinci terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Yerel örnek ayarlarda `AUTH_DISABLED=true` kullanılır ve bütün işlemler `Planlama Kullanıcısı` adına kaydedilir.

## Geri bildirim akışı

- Her sayfada tek bir **Geri bildirim** düğmesi bulunur.
- Kullanıcı yalnızca notunu yazar, görsel ekler veya sesli not kaydeder.
- Bulunulan sayfa backend'e sessizce eklenir; formda gösterilmez.
- **Geri Bildirimler** sayfasında geçmiş notlar, konuşmalar ve ekler birlikte görünür.
- Bir not düzenlenebilir, yorumlanabilir, çözülebilir, iptal edilebilir veya yeniden açılabilir.
- Yorumlar düzenlenebilir.
- Görseller ve ses kayıtları yetkili API üzerinden okunur; doğrudan herkese açık dosya adresleri kullanılmaz.
- Ekler geri bildirim sayfasından silinebilir.

Ayrıntılı davranış: [`docs/feedback-workflow.md`](docs/feedback-workflow.md).

## Clerk

Üretimde:

1. frontend'e `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` ekleyin;
2. backend'de `AUTH_DISABLED=false` yapın;
3. `CLERK_ISSUER_URL`, `CLERK_JWKS_URL` ve `CLERK_AUTHORIZED_PARTIES` değerlerini doldurun;
4. frontend ve backend ortamlarında CORS/API adreslerini gerçek alan adlarıyla değiştirin.

Frontend Clerk oturum jetonunu her API isteğinde `Bearer` olarak gönderir. FastAPI jeton imzasını Clerk JWKS üzerinden, issuer ve isteğe bağlı authorized-party/audience kontrolleriyle doğrular. Kullanıcı kimliği frontend tarafından gönderilen serbest metne güvenilerek değil, doğrulanmış jeton claim'lerinden oluşturulur.

## Dağıtım notu

Frontend Vercel üzerinde çalışabilir. Mevcut backend yerel SQLite ve yerel dosya deposu kullanır; bu nedenle üretimde backend'i kalıcı disk sağlayan bir serviste çalıştırın. Sunucusuz/ephemeral bir backend kullanılacaksa SQLite'ın yönetilen PostgreSQL'e, `backend/data/uploads` klasörünün de S3 uyumlu nesne depolamaya taşınması gerekir.

## Testler

```bash
cd frontend && npm test && npm run build
cd ../backend && .venv/bin/python -m pytest -q
```

## Excel verisini yenileme

```bash
cd frontend
python3 scripts/extract_workbook.py ../Tezgah_Planlama_V51.xlsm data/workbook.json
python3 scripts/build_planning_seed.py data/workbook.json data/planning-seed.json
npm test
```

