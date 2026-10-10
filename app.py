"""
ЧистеФото — інтерфейс (Streamlit), дизайн перенесено з макета Figma.

Три екрани (кроки зі степпера у макеті):
  1. Завантаження — користувач додає фото речі;
  2. Обробка      — AI прибирає фон (спінер + пояснення);
  3. Результат    — порівняння «до / після» і кнопка «Завантажити PNG».
Поточний екран і результат зберігаються в st.session_state.
"""

import io
from pathlib import Path

import streamlit as st
from PIL import Image, UnidentifiedImageError

from ai_functions import on_white_background, remove_background, to_png_bytes

st.set_page_config(page_title="ЧистеФото", page_icon="📸", layout="wide")
st.markdown(f"<style>{Path(__file__).with_name('styles.css').read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)


def icon(paths, size=18, color="currentColor"):
    body = "".join(f'<path d="{p}"/>' for p in paths)
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')

ICON_SCAN = ["M3 7V5a2 2 0 0 1 2-2h2", "M17 3h2a2 2 0 0 1 2 2v2", "M21 17v2a2 2 0 0 1-2 2h-2",
             "M7 21H5a2 2 0 0 1-2-2v-2", "M7 12h10"]
ICON_CHECK = ["M20 6 9 17l-5-5"]
ICON_INFO = ["M12 16v-4", "M12 8h.01", "M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0z"]
ICON_HELP = ["M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0z", "M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3", "M12 17h.01"]
ICON_SPARK = ["M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"]
ICON_FILE = ["M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z", "M14 3v6h6"]
GREEN, GRAY = "#267a50", "#718078"


ss = st.session_state
ss.setdefault("step", "upload")      
ss.setdefault("photo", None)        
ss.setdefault("photo_name", "")
ss.setdefault("result", None)       


def go(step):
    ss.step = step


def reset():
    ss.step, ss.photo, ss.photo_name, ss.result = "upload", None, "", None


def photo_info(data, name):
    """Метадані фото для картки файлу: розміри, формат, вага."""
    img = Image.open(io.BytesIO(data))
    size_kb = len(data) / 1024
    size = f"{size_kb / 1024:.1f} МБ".replace(".", ",") if size_kb > 1024 else f"{size_kb:.0f} КБ"
    return img.width, img.height, (img.format or "").replace("JPEG", "JPG"), size


def header():
    st.markdown(f"""
    <div class="app-header">
      <div class="identity">
        <div class="brand-mark">{icon(ICON_SCAN, 24, "#fff")}</div>
        <span class="product-name">ЧистеФото</span><span class="divider-v"></span>
        <span class="product-desc">Річ у фокусі. Фон — білий.</span>
      </div>
      <div class="help">{icon(ICON_HELP, 18, GRAY)}<span>Як це працює</span></div>
    </div><div class="header-gap"></div>""", unsafe_allow_html=True)


def stepper(active):
    labels = ["Завантаж фото", "Прибери фон", "Збережи результат"]
    html = '<div class="workflow">'
    for i, label in enumerate(labels, 1):
        cls = "done" if i < active else "active" if i == active else ""
        mark = icon(ICON_CHECK, 16, "#fff") if i < active else str(i)
        conn = '<span class="connector"></span>' if i < len(labels) else ""
        html += f'<div class="step {cls}"><span class="marker">{mark}</span><span>{label}</span>{conn}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def title(text, subtitle, badge=False):
    b = f'<span class="badge">{icon(ICON_CHECK, 14, GREEN)}Фон прибрано</span>' if badge else ""
    st.markdown(f'<div><h1 class="page-title">{text}{b}</h1><p class="page-subtitle">{subtitle}</p></div>',
                unsafe_allow_html=True)


def footer():
    st.markdown('<div class="app-footer"><span>Менше редагування. Більше часу на твої справи.</span>'
                '<span>Одна річ · Білий фон · PNG</span></div>', unsafe_allow_html=True)


def screen_upload():
    stepper(1)
    title("Фото речі. Без зайвого фону.",
          "Завантаж знімок — і отримай фото на білому фоні приблизно за пів хвилини.")
    left, right = st.columns([744, 352], gap="medium")
    with left:
        with st.container(key="card_upload"):
            uploaded = st.file_uploader("Фото речі", type=["jpg", "jpeg", "png"],
                                        label_visibility="collapsed")
            valid = False
            if uploaded is not None:
                try:
                    # Перевіряємо, що файл справді відкривається як фото.
                    Image.open(io.BytesIO(uploaded.getvalue())).verify()
                    valid = True
                except Exception:
                    st.error("Не вдалося відкрити цей файл як фото. "
                             "Спробуй інший знімок у форматі JPG або PNG.")
            hint, btn = st.columns([1, 1])
            with hint:
                if uploaded is None:
                    st.markdown(f'<div class="hint">{icon(ICON_INFO, 16, GRAY)}'
                                'Спочатку завантаж фото речі</div>', unsafe_allow_html=True)
            with btn:
                with st.container(key="go_empty" if not valid else "go_ready"):
                    clicked = st.button("Прибрати фон", icon=":material/auto_awesome:",
                                        type="primary" if valid else "secondary",
                                        use_container_width=True)
            if clicked:
                if uploaded is None:
                    # Перевірка вводу ДО звернення до AI: без фото функцію не викликаємо.
                    st.warning("Спочатку завантаж фото речі — без нього мені нічого обробляти. 📷")
                elif valid:
                    ss.photo, ss.photo_name = uploaded.getvalue(), uploaded.name
                    go("process")
                    st.rerun()
    with right:
        with st.container(key="card_guide"):
            st.markdown(f"""
            <div class="guide-title">Для вдалого знімка</div>
            <div class="advice">Поклади річ на простий фон і сфотографуй при денному світлі.
            Нехай предмет повністю потрапить у кадр.</div>
            <div class="guide-h">Далі все просто</div>
            <div class="guide-item"><span class="guide-ico">1</span><div><div class="t">AI прибере зайве</div>
              <div class="d">Відокремить річ від фону.</div></div></div>
            <div class="guide-item"><span class="guide-ico">2</span><div><div class="t">Фон стане білим</div>
              <div class="d">Уся увага — на твоїй речі.</div></div></div>
            <div class="guide-item"><span class="guide-ico">3</span><div><div class="t">Збережи PNG</div>
              <div class="d">Для оголошення на OLX чи Instagram.</div></div></div>""",
                        unsafe_allow_html=True)

def screen_process():
    stepper(2)
    title("Твоя річ — у центрі уваги",
          "Фото завантажено. Зараз приберемо все зайве й залишимо білий фон.")
    w, h, fmt, size = photo_info(ss.photo, ss.photo_name)
    left, right = st.columns([744, 352], gap="medium")
    with left:
        with st.container(key="card_original"):
            st.markdown('<div class="card-row"><span class="card-title">Оригінал</span>'
                        '<span class="small">Фото завантажено</span></div>', unsafe_allow_html=True)
            st.image(ss.photo, use_container_width=True)
            st.markdown(f'<div class="file-info"><span class="file-symbol">{icon(ICON_FILE, 19, GREEN)}</span>'
                        f'<div><div class="file-name">{ss.photo_name}</div>'
                        f'<div class="file-meta">{w} × {h} px · {fmt} · {size}</div></div></div>',
                        unsafe_allow_html=True)
    with right:
        with st.container(key="card_panel"):
            st.markdown(f"""
            <div class="tool-symbol">{icon(ICON_SPARK, 24, GREEN)}</div>
            <div class="panel-title">Чистий фон, без зусиль</div>
            <div class="panel-text">Збережемо твою річ і замінимо фон на білий. Нічого не потрібно налаштовувати.</div>
            <div class="status-box" style="margin-top:24px"><div class="spin"></div>
              <div class="status-msg">AI вирізає предмет із фону…</div>
              <div class="panel-text" style="font-size:13px">Зазвичай це займає до 30 секунд. Залиш цю сторінку відкритою.</div>
              <div class="progress"><span></span></div></div>
            <div class="hint" style="margin-top:24px">Потім порівняєш фото й завантажиш результат.</div>""",
                        unsafe_allow_html=True)
    st.markdown(f'<div class="hint">{icon(ICON_INFO, 16, GRAY)}Твій оригінал залишається без змін.</div>',
                unsafe_allow_html=True)

    try:
        with st.spinner("AI вирізає предмет із фону — це займе кілька секунд…"):
            cutout = remove_background(ss.photo)
            ss.result = to_png_bytes(on_white_background(cutout))
    except UnidentifiedImageError:
        st.error("Не вдалося відкрити цей файл як фото. Спробуй інший знімок у форматі JPG або PNG.")
        st.button("Спробувати інше фото", on_click=reset)
        return
    except Exception:
        st.error("Щось пішло не так, і фон прибрати не вдалося. Перевір інтернет "
                 "(під час першого запуску потрібне завантаження моделі) і спробуй ще раз за хвилину.")
        st.button("Спробувати інше фото", on_click=reset)
        return
    go("result")
    st.rerun()


def screen_result():
    stepper(3)
    title("Готово! Тільки річ, тільки білий фон.",
          "Порівняй із оригіналом і збережи фото для свого оголошення.", badge=True)
    w, h, _, _ = photo_info(ss.photo, ss.photo_name)
    before, after = st.columns(2, gap="medium")
    with before:
        with st.container(key="card_before"):
            st.markdown('<div class="card-row"><span class="card-title">Оригінал</span>'
                        '<span class="small">До обробки</span></div>', unsafe_allow_html=True)
            st.image(ss.photo, use_container_width=True)
            st.markdown('<div class="small" style="margin-top:14px">Твоє фото з початковим фоном.</div>',
                        unsafe_allow_html=True)
    with after:
        with st.container(key="card_after"):
            st.markdown(f'<div class="card-row"><span class="card-title">Результат</span>'
                        f'<span class="small accent">{icon(ICON_CHECK, 14, GREEN)} Білий фон</span></div>',
                        unsafe_allow_html=True)
            st.markdown('<div class="white-frame">', unsafe_allow_html=True)
            st.image(ss.result, use_container_width=True)
            st.markdown('</div><div class="small" style="margin-top:14px">'
                        'Та сама річ. Нічого зайвого навколо.</div>', unsafe_allow_html=True)

    with st.container(key="card_download"):
        info, action = st.columns([4, 1], vertical_alignment="center")
        with info:
            st.markdown(f'<div class="file-info" style="margin:0"><span class="file-symbol big">'
                        f'{icon(ICON_FILE, 24, GREEN)}</span><div><div class="dl-name">chyste_foto.png</div>'
                        f'<div class="dl-meta">PNG · {w} × {h} px · білий фон</div></div></div>',
                        unsafe_allow_html=True)
        with action:
            st.download_button("Завантажити PNG", data=ss.result, file_name="chyste_foto.png",
                               mime="image/png", icon=":material/download:", type="primary",
                               use_container_width=True)
    ready, restart = st.columns([4, 1], vertical_alignment="center")
    with ready:
        st.markdown(f'<div class="hint">{icon(ICON_CHECK, 18, GREEN)}Фото готове для OLX та Instagram.</div>',
                    unsafe_allow_html=True)
    with restart:
        st.button("Почати знову", icon=":material/restart_alt:", on_click=reset, use_container_width=True)


header()
{"upload": screen_upload, "process": screen_process, "result": screen_result}[ss.step]()
footer()
