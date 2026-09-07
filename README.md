# Selsa Planlama — planlama ve geri bildirim çalışma alanı

Proje artık iki bağımsız uygulamadan oluşur:

- `frontend/`: Next.js üretim planlama arayüzü ve ortak geri bildirim sayfası
- `backend/`: FastAPI, Clerk oturum doğrulaması, rol yetkilendirmesi, SQLite verisi, görseller ve sesli notlar

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

## Staging çalışma alanı

Günlük geliştirme artık iki repodaki `staging` dalında ve üretimden ayrılmış yerel staging verisiyle yapılır.

Backend staging ortamını başlatmak için:

```bash
./scripts/run-staging.sh
```

Bu komut `backend/.env` dosyasını kullanır ve API'yi `http://127.0.0.1:8001` adresinde açar. Yerel staging ayarları `data/staging.sqlite` ve `data/uploads-staging` yollarını kullanır; üretim verisiyle paylaşılmaz. Yeni bir ortam kurarken `.env.staging.example` dosyasını gizli değerleri repoya eklemeden örnek alın.

Frontend ayrı terminalde `npm run dev:staging` ile `http://localhost:3001` adresinde çalıştırılır.

Dağıtılmış staging ortamında aşağıdaki değerleri platformun secret/environment ayarlarında tanımlayın:

- `APP_ENV=staging`
- staging Clerk uygulamasının `CLERK_ISSUER`, `CLERK_AUTHORIZED_PARTIES` ve tercihen `CLERK_JWT_KEY` değerleri
- kalıcı diskte staging'e özel `DATABASE_PATH` ve `UPLOAD_DIR`
- yalnızca staging frontend adresini içeren `CORS_ORIGINS`
- üretim API kök adresini içeren `PRODUCTION_API_URL` (ör. `https://api.planning.hfgok.com/api`)
- üretimdeki `STAGING_PULL_TOKEN` ile eşleşen, yalnız backend'de tutulan `PRODUCTION_SYNC_TOKEN`

Üretim backend'inde ayrıca uzun ve rastgele bir `STAGING_PULL_TOKEN` tanımlayın. Bu anahtar yalnızca staging'in salt okunur üretim anlık görüntüsünü almasına izin verir. Staging'in üretime yazabildiği bir endpoint yoktur; `POST /api/production-sync/pull` yalnız `APP_ENV=staging` ortamında çalışır ve staging verisini son kaynak tabanıyla karşılaştırarak atomik olarak uzlaştırır; yerelde değişen operasyonel kayıtlar birlikte korunur, değişmemiş kaynak alanları yenilenir.

`APP_ENV=staging` veya `production` iken `CLERK_ISSUER` eksikse uygulama başlamaz.

Hetzner staging dağıtımı için repodaki `deploy/` şablonları staging backend'i `/root/planning-automation-backend-staging` altında, `8003` iç portunda ve `api-staging.planning.hfgok.com` alan adında üretim servisinden ayrı çalıştırır.

Frontend ve backend aynı Clerk instance'ını kullanmalıdır. Backend Clerk'in RS256 oturum jetonunu `CLERK_JWT_KEY` ile ağ erişimi olmadan veya instance JWKS adresinden doğrular. `CLERK_AUTHORIZED_PARTIES` yalnız gerçek frontend adreslerini içermelidir.

## Geri bildirim akışı

- Her sayfada tek bir **Geri bildirim** düğmesi bulunur.
- Kullanıcı yalnızca notunu yazar, görsel ekler veya sesli not kaydeder.
- Bulunulan sayfa backend'e sessizce eklenir; formda gösterilmez.
- **Geri Bildirimler** sayfasında geçmiş notlar, konuşmalar ve ekler birlikte görünür.
- Bir not düzenlenebilir, yorumlanabilir, çözülebilir, iptal edilebilir veya yeniden açılabilir.
- `POST /api/order-imports/preview`, `Tip no` ve `Sipariş Adeti` kolonlu `.xlsx` sipariş dosyasını veri değişikliği yapmadan doğrular ve önizleme özeti döndürür.
- Excel önizleme servisi yüklenen dosyayı bellekte okur; proje kökündeki `tipler.xlsx` veya başka bir sabit dosya yoluna bağlı değildir. Backend ayrı bir repodan dağıtılabilir.
- Yorumlar düzenlenebilir.
- Görseller ve ses kayıtları yetkili API üzerinden okunur; doğrudan herkese açık dosya adresleri kullanılmaz.
- Ekler geri bildirim sayfasından silinebilir.

Ayrıntılı davranış: [`../frontend/docs/feedback-workflow.md`](../frontend/docs/feedback-workflow.md).

## Clerk erişimi ve roller

Clerk Dashboard'da uygulamayı **Invite-only** moda alın ve kullanıcıları şirket e-posta adresleriyle davet edin. Session token'a `fullName`, `primaryEmail` ve `metadata` taleplerini ekleyin; tam örnek frontend README dosyasındadır.

Her kullanıcı varsayılan olarak `user` rolündedir. Sunucudaki e-posta rol tablosunda yönetici kaydı varsa bu da yönetici yetkisi verir; normal kullanıcı erişiminde bu kaydın bulunmadığı doğrulanmalıdır. Yönetici hesabının Clerk public metadata alanına `{ "role": "admin" }` yazılır. İlk yönetici ayrıca geçici olarak `CLERK_ADMIN_USER_IDS` ile atanabilir. Backend imzalı talepten rolü okur; frontend kontrolünden bağımsız olarak Ayarlar değişikliklerini, ayar paketi işlemlerini, uygulama güncellemesi yayınlamayı ve staging üretim senkronizasyonunu yalnız yöneticilere açar.

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

## Restarting
```bash
sudo systemctl restart planning-automation-backend
```

Then verify it started correctly:

```bash
systemctl status planning-automation-backend --no-pager
```

Staging
```bash
sudo systemctl restart planning-automation-backend-staging
```

## Ravi

Ravi setup, tools, source-map maintenance and validation: [workspace guide](../docs/ravi.md).
