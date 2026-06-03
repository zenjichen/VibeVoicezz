# Huong dan chay tren may moi

Muc tieu: clone repo tu GitHub ve may Windows khac va chay GUI ma khong phu thuoc vao moi truong cua may cu.

## Dieu kien can co

- Windows 10/11 64-bit.
- Python 3.11 da cai va co lenh `py -3.11` hoac `python` trong PATH.
- Git de clone source.
- Internet cho lan chay dau tien. Script se tai Python packages va model tu Hugging Face.
- O dia con trong toi thieu 15-25 GB, vi PyTorch va model TTS kha lon.
- GPU NVIDIA la tot nhat. Khong co GPU van co the chon `cpu` trong GUI nhung se cham hon nhieu.

## Cach chay

```bat
git clone <URL_REPO_CUA_BAN>
cd VibeVoicezz
run_gui.bat
```

Lan dau `run_gui.bat` se tu tao `.venv`, cai dependency cua project bang `pip install -e .`, sau do mo `gui.py`.

Repo co the dat o Desktop, o D/E, hoac thu muc tuy bien. Cac file noi bo nhu preset, settings, audio library va cache se duoc tim theo thu muc chua `gui.py`, khong theo thu muc hien tai cua Command Prompt.

Neu tao shortcut, tro shortcut vao `run_gui.bat`. Script nay tu `cd` ve dung thu muc repo truoc khi chay app.

## Khong commit cac file nay

Nhung file/thu muc sau la du lieu sinh ra theo tung may va da duoc dua vao `.gitignore`:

- `.venv/`
- `__pycache__/`
- `generated_audios/`
- `voice_prompt_cache/`
- `gui_settings.json`
- `recorded_temp.wav`

Neu cac file nay bi dua len GitHub, may khac de loi vi virtualenv va cache co duong dan/package rieng cua may cu.

## Luu y ve preset voice

Preset mau trong `voice_presets.json` dung duong dan relative:

```json
"m\u1eabu voice/Nguy\u1ec7t \u00c1nh.mp3"
```

Viec nay giup preset van dung duoc sau khi clone repo sang thu muc khac, mien la file audio mau van nam trong thu muc `mau voice` cua repo.
