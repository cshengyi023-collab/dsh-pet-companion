// 从桌宠的 webm 动画里抽一帧（带透明通道）→ PNG
// 用法: electron.exe extract_frame.js <in.webm> <out.png> [seekSeconds]
const { app, BrowserWindow } = require('electron');
const fs = require('fs');
const os = require('os');
const path = require('path');

const input = process.argv[2];
const output = process.argv[3];
const seek = Number(process.argv[4] || '1.2');
const toFileUrl = (p) => encodeURI('file:///' + p.replace(/\\/g, '/'));

app.whenReady().then(async () => {
  let htmlPath = null;
  try {
    const b64 = fs.readFileSync(input).toString('base64');
    const dataUri = 'data:video/webm;base64,' + b64;
    htmlPath = path.join(os.tmpdir(), 'dsh-pet-frame-' + Date.now() + '.html');
    fs.writeFileSync(
      htmlPath,
      `<!doctype html><html><body style="margin:0;background:transparent">
         <video id="v" muted preload="auto"></video>
       </body></html>`,
      'utf8',
    );
    const win = new BrowserWindow({
      show: false,
      width: 640,
      height: 360,
      webPreferences: { offscreen: false, backgroundThrottling: false, webSecurity: false },
    });
    await win.loadFile(htmlPath);
    const dataUrl = await win.webContents.executeJavaScript(`(async () => {
      const v = document.querySelector('#v');
      if (!v) throw new Error('no video element');
      v.src = ${JSON.stringify(dataUri)};
      v.load();
      await new Promise((res, rej) => {
        if (v.readyState >= 2) return res();
        v.addEventListener('loadeddata', () => res(), { once: true });
        v.addEventListener('error', () => rej(new Error('video error=' + (v.error ? v.error.code + ':' + v.error.message : 'unknown'))), { once: true });
        setTimeout(() => rej(new Error('video load timeout readyState=' + v.readyState)), 15000);
      });
      const dur = Number.isFinite(v.duration) ? v.duration : 0;
      const t = Math.min(${seek}, dur > 0 ? dur * 0.5 : ${seek});
      try { v.currentTime = t; } catch (e) {}
      await new Promise((res) => {
        let done = false;
        const fin = () => { if (done) return; done = true; res(); };
        v.addEventListener('seeked', fin, { once: true });
        setTimeout(fin, 1500);
      });
      const c = document.createElement('canvas');
      c.width = v.videoWidth || 640;
      c.height = v.videoHeight || 360;
      const ctx = c.getContext('2d');
      ctx.clearRect(0, 0, c.width, c.height);
      ctx.drawImage(v, 0, 0, c.width, c.height);
      return c.toDataURL('image/png');
    })()`);
    fs.writeFileSync(output, Buffer.from(dataUrl.split(',')[1], 'base64'));
    console.log('frame written:', output, fs.statSync(output).size, 'bytes');
    app.exit(0);
  } catch (e) {
    console.error('FAILED:', e && e.message ? e.message : e);
    app.exit(1);
  } finally {
    try { if (htmlPath) fs.unlinkSync(htmlPath); } catch (e) {}
  }
});
