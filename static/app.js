const form = document.querySelector('#translate-form');
const fileInput = document.querySelector('#file');
const zone = document.querySelector('#dropzone');
const result = document.querySelector('#result');
const title = document.querySelector('#result-title');
const statusText = document.querySelector('#status');
const download = document.querySelector('#download');
const report = document.querySelector('#report');
let url;
function selected() {
  const file = fileInput.files[0];
  document.querySelector('#file-label').textContent = file ? file.name : 'Kéo thả tài liệu vào đây';
  document.querySelector('#file-meta').textContent = file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · ${file.name.split('.').pop().toUpperCase()}` : '';
}
fileInput.addEventListener('change', selected);
for (const event of ['dragenter', 'dragover']) zone.addEventListener(event, e => {e.preventDefault(); zone.classList.add('dragging');});
for (const event of ['dragleave', 'drop']) zone.addEventListener(event, e => {e.preventDefault(); zone.classList.remove('dragging');});
zone.addEventListener('drop', e => {
  if (e.dataTransfer.files.length) {fileInput.files = e.dataTransfer.files; selected();}
});
form.addEventListener('submit', async e => {
  e.preventDefault();
  const button = document.querySelector('#submit');
  result.hidden = false; download.hidden = true; report.textContent = '';
  title.textContent = 'Đang dịch tài liệu…';
  statusText.textContent = 'Vui lòng giữ trang mở. Tài liệu dài có thể mất vài phút.';
  const file = fileInput.files[0];
  if (!file || file.size > 20 * 1024 * 1024 || !/\.(docx|pdf|txt)$/i.test(file.name)) {
    title.textContent = 'Kiểm tra tài liệu'; statusText.textContent = 'Chọn file DOCX, PDF hoặc TXT, tối đa 20 MB.'; return;
  }
  button.disabled = true;
  try {
    const response = await fetch('/translate', {method: 'POST', body: new FormData(form), headers: {'X-App-Token': document.body.dataset.token}});
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || 'Không nhận được kết quả. Hãy thử lại.');
    }
    const blob = await response.blob();
    if (url) URL.revokeObjectURL(url);
    url = URL.createObjectURL(blob);
    download.href = url; download.download = file.name.replace(/(\.[^.]+)$/, '_vi$1'); download.hidden = false;
    title.textContent = 'Bản dịch đã sẵn sàng';
    statusText.textContent = 'Tải file và đối chiếu với tài liệu gốc trước khi sử dụng.';
    const summary = JSON.parse(response.headers.get('X-Translation-Report') || '{}');
    report.textContent = file.name.toLowerCase().endsWith('.pdf')
      ? `Đã dịch ${summary.blocks} vùng trên ${summary.pages} trang. Giữ nguyên ${summary.protected_blocks} vùng có dấu hiệu toán học/chữ xoay. PDF có thể đổi font, cỡ chữ và kiểu nhấn mạnh.`
      : `Đã cập nhật ${summary.text_runs} đoạn chữ. Giữ nguyên ${summary.skipped_fields} đoạn chứa trường tự động và ${summary.protected_paragraphs || 0} đoạn có LaTeX bị chia nhỏ. Kiểm tra lại ngắt dòng và số trang.`;
  } catch (error) {
    title.textContent = 'Chưa thể hoàn tất'; statusText.textContent = error.message;
  } finally {button.disabled = false; document.querySelector('#api-key').value = '';}
});
