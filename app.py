"""
ЧистеФото — інтерфейс (Streamlit).

Головний сценарій: користувач завантажує фото речі → натискає кнопку →
AI прибирає фон → бачить результат на білому тлі й може його завантажити.
"""

import streamlit as st

from ai_functions import on_white_background, remove_background, to_png_bytes


st.set_page_config(page_title="ЧистеФото", page_icon="📸")
st.title("📸 ЧистеФото")
st.caption(
    "Допомагаю продавцям на OLX і в Instagram зробити чисте фото речі "
    "на білому фоні за пів хвилини — за допомогою AI."
)


uploaded = st.file_uploader("Завантаж фото речі", type=["jpg", "jpeg", "png"])

if uploaded is not None:
    st.image(uploaded, caption="Оригінал", use_container_width=True)


if st.button("✨ Прибрати фон"):
    if uploaded is None:
        # Мінімальна перевірка вводу: без фото функцію не викликаємо.
        st.warning("Спочатку завантаж фото речі.")
    else:
        with st.spinner("AI вирізає предмет з фону…"):
            cutout = remove_background(uploaded.getvalue())
            final = on_white_background(cutout)
        st.subheader("Результат")
        st.image(final, caption="Фото на білому фоні", use_container_width=True)
        st.download_button(
            "⬇️ Завантажити PNG",
            data=to_png_bytes(final),
            file_name="chyste_foto.png",
            mime="image/png",
        )
