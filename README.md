# THI247 Learning Hub — PWA + Android starter

Kho dữ liệu học tập miễn phí, dùng chung cho Web/PWA và Android (Capacitor). Đây là **bộ khung triển khai**, không phải bản đã quét/tải toàn bộ THI247.com. Crawler mặc định chỉ lập chỉ mục metadata và liên kết công khai; không tải hàng loạt PDF, không vượt đăng nhập/CAPTCHA/paywall, và tôn trọng robots.txt/điều khoản website.

## Tính năng trong bộ khung
- Crawler Python có giới hạn tốc độ, timeout, giới hạn trang, domain allowlist, robots.txt và user-agent nhận diện.
- Schema JSONL cho tài nguyên và CSV xuất danh mục.
- Gắn trạng thái quyền sử dụng (`metadata_only`, `link_only`, `permission_granted`, `public_domain`, `unknown`, `restricted`).
- PWA tiếng Việt, tìm kiếm/lọc theo lớp, môn, loại tài liệu; cache shell offline.
- Capacitor Android và GitHub Actions tạo debug APK.
- Không chép nội dung có bản quyền vào app chỉ vì tài liệu truy cập miễn phí.

## Yêu cầu
- Node.js 20+ và npm
- Python 3.11+
- Android build trên GitHub Actions (Ubuntu + Java 21); build local cần Android Studio/SDK.

## Chạy crawler (metadata/index)
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r crawler/requirements.txt
python crawler/crawl.py --start https://thi247.com/ --max-pages 100 --delay 2 --out data/catalog.jsonl
python crawler/export_csv.py data/catalog.jsonl data/catalog.csv
python crawler/export_json.py data/catalog.jsonl public/data/catalog.json
```

`--max-pages` mặc định 100; tăng dần sau khi kiểm tra robots.txt, điều khoản, tải máy chủ và quyền sử dụng. Không dùng đồng thời nhiều worker. Crawler có thể không tìm được link ẩn bằng JavaScript hoặc bị giới hạn bởi website; kiểm tra log và danh mục thủ công.

## Chạy PWA
```bash
npm install
npm run dev
```
Mở URL Vite được hiển thị. Để build:
```bash
npm run build
```
Deploy thư mục `dist/` lên host static HTTPS (ví dụ GitHub Pages/Netlify). GitHub Pages cần cấu hình base path nếu deploy dưới subpath.

## Android APK
```bash
npm install
npm run cap:sync
npx cap open android
```
Trong Android Studio chọn Build > Build APK(s), hoặc push lên GitHub để chạy workflow `.github/workflows/build-apk.yml`. APK debug sẽ xuất hiện trong Actions > workflow run > Artifacts. APK debug chỉ để thử nghiệm, không phải bản phát hành ký bằng khóa release.

## Chính sách dữ liệu
- Chỉ lưu metadata tối thiểu và URL nguồn cho tài liệu chưa được cấp quyền tái phân phối.
- Không tải hoặc lưu trữ bản sao PDF/ảnh/nội dung đầy đủ khi chưa xác minh giấy phép/quyền.
- Chỉ chuyển `rights_status` sang `permission_granted` sau khi có bằng chứng giấy phép/cho phép bằng văn bản.
- Đối với nội dung dẫn link ngoài, mở trang nguồn; không gỡ watermark, quảng cáo, DRM hay cơ chế kiểm soát truy cập.
- Cho phép chủ sở hữu yêu cầu sửa/xóa liên kết; ghi `checked_at`, `source_url`, `rights_evidence_url`.

## Trạng thái
Đây là starter repo. Cần chạy crawler thực tế, kiểm tra điều khoản/robots.txt, rà soát chất lượng và quyền sử dụng trước khi phát hành. Không có cam kết rằng toàn bộ website đã được lập chỉ mục.

## Trước khi bật lịch crawl tự động
1. Mở `https://thi247.com/robots.txt` và đọc điều khoản sử dụng/chính sách bản quyền của website.
2. Nếu robots.txt không truy cập được hoặc không rõ quyền, không bật workflow tự động; chỉ dùng danh mục link nhập thủ công cho đến khi làm rõ.
3. Chạy lần đầu với `--max-pages 20 --delay 3`, kiểm tra log, trang được thu thập và mức tải.
4. Crawler không tự xác định lớp/môn một cách chắc chắn; cần bước phân loại/duyệt thủ công.
5. Workflow lịch dùng metadata công khai và có giới hạn 100 trang/lần. Điều chỉnh chỉ sau khi xác minh được phép và website không phản đối.

## App icon and UI settings
- PWA icons: `public/icons/icon-192.png`, `public/icons/icon-512.png`, `public/icons/apple-touch-icon.png`.
- Android foreground artwork reference: `android-assets/icon-foreground.svg`. Capacitor's generated Android launcher icon may still need to be copied into Android mipmap resources using Android Studio's Image Asset tool after `npx cap add android`.
- Settings screen supports Light / Dark / System, five accent colors, and Small / Medium / Large font size. Preferences are saved locally in the browser/device.
- The icon PNGs and SVG are project assets; replace them if you have a brand-approved final logo.

## Push to GitHub
1. Create a new empty GitHub repository.
2. Extract the ZIP and upload the *contents* of the project root (including `.github/`) to the repository root.
3. Commit to `main`.
4. Open Actions and run `Build Android APK`; download the `kho-hoc-tap-debug-apk` artifact after success.
5. Open `Refresh public metadata catalog` manually only after reviewing `robots.txt`, terms, and permission. The default schedule is weekly and limited to 100 HTML pages per run.
