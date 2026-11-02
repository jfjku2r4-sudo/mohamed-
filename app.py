import streamlit as st
import json
import re
import random
import hashlib
import time
import tempfile
from pathlib import Path

# محاولة استيراد مكتبة قراءة ملفات PDF واستخراج النص منها
try:
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    try:
        import PyPDF2 as pypdf
        PDF_SUPPORT = True
    except ImportError:
        PDF_SUPPORT = False

# مكتبة Gemini الحديثة
try:
    from google import genai
    GEMINI_SUPPORT = True
except ImportError:
    genai = None
    GEMINI_SUPPORT = False

# إعداد كلمة مرور الدخول
# يمكنك وضع APP_PASSWORD في Streamlit Secrets
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "01224982634")

# إعدادات الصفحة
st.set_page_config(
    page_title="منصة امتحانات الثانوية العامة الذكية | Mohamed Abdallah",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم الواجهة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }

    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #2563eb, #7c3aed, #db2777);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 900;
        margin-bottom: 5px;
    }

    .sub-header {
        font-size: 1.15rem;
        text-align: center;
        margin-bottom: 25px;
        font-weight: 600;
    }

    .bright-card {
        padding: 25px;
        border-radius: 18px;
        border: 2px solid rgba(59, 130, 246, 0.2);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
        position: relative;
    }

    .exam-watermark {
        position: absolute;
        right: 15px;
        bottom: 10px;
        font-size: 0.75rem;
        opacity: 0.6;
        font-weight: bold;
        pointer-events: none;
    }

    .footer {
        text-align: center;
        margin-top: 40px;
        font-size: 1rem;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
        padding-top: 20px;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# إدارة حالة الجلسة
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "hints_used" not in st.session_state:
    st.session_state.hints_used = 0

if "unlocked_hints" not in st.session_state:
    st.session_state.unlocked_hints = set()

# --- صفحة تسجيل الدخول ---
if not st.session_state.logged_in:

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown(
        "<div class='main-header'>🔐 بوابة الدخول للمنصة الذكية</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='sub-header'>قم بتسجيل الدخول للوصول لكافة الامتحانات والشات الذكي وتحليل الملفات والقوانين</div>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("<div class='bright-card'>", unsafe_allow_html=True)

        with st.form("login_form"):

            input_name = st.text_input(
                "👤 اسم الطالب الثلاثي",
                placeholder="اكتب اسمك الثلاثي..."
            )

            password = st.text_input(
                "🔑 كلمة المرور",
                type="password",
                placeholder="أدخل كلمة المرور..."
            )

            remember_me = st.checkbox(
                "حفظ الجلسة والتسجيل في هذا المتصفح",
                value=True
            )

            submit_login = st.form_submit_button("دخول المنصة 🚀")

            if submit_login:

                if password == APP_PASSWORD and input_name.strip() != "":
                    st.session_state.logged_in = True
                    st.session_state.username = input_name.strip()

                    st.success(
                        f"✨ أهلاً بك يا {st.session_state.username}! جاري فتح المنصة..."
                    )

                    st.rerun()

                elif password != APP_PASSWORD:
                    st.error("❌ كلمة المرور غير صحيحة.")

                else:
                    st.warning("⚠️ يرجى كتابة اسمك الثلاثي أولاً.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='footer'>حقوق الملكية والتطوير محفوظة © "
        "<b>محمد عبدالله - Mohamed Abdallah</b> 💻</div>",
        unsafe_allow_html=True
    )

else:

    # --- القائمة الجانبية ---
    with st.sidebar:

        st.image(
            "https://img.icons8.com/clouds/200/graduation-cap.png",
            width=100
        )

        st.markdown(
            f"### 👤 الطالب: **{st.session_state.username}**"
        )

        st.markdown("---")

        st.header("⚙️ إعدادات النموذج والاختبار")
        st.caption("⚡ وضع الاستجابة السريعة مفعّل")

        api_key = st.text_input(
            "🔑 مفتاح Gemini API Key:",
            type="password",
            help="أدخل مفتاح Google Gemini API"
        )

        model_choices = {
            "⚡ Gemini 3.5 Flash-Lite — الأسرع للردود والاختبارات": "gemini-3.5-flash-lite",
            "🚀 Gemini 3.1 Flash-Lite — سريع واقتصادي": "gemini-3.1-flash-lite",
            "⚖️ Gemini 3.6 Flash — توازن بين السرعة والجودة": "gemini-3.6-flash",
            "🧠 Gemini 3.8 Flash — جودة أعلى للمهام المعقدة": "gemini-3.8-flash",
        }

        selected_model_label = st.selectbox(
            "🤖 اختر نموذج الذكاء الاصطناعي (الأسرع أولاً):",
            options=list(model_choices.keys()),
            index=0,
            help="يبدأ الاختيار تلقائياً بأسرع نموذج. يمكنك اختيار نموذج أقوى عند الحاجة."
        )

        exam_type = st.radio(
            "📋 نوع إنشاء الاختبار:",
            [
                "🚀 اختبار شامل للمادة",
                "🎯 اختبار واحد (مستوى مخصص)",
                "🔥 3 اختبارات (سهل، متوسط، صعب)",
                "📐 اختبار قوانين وتطبيقات (من ملف القوانين)"
            ]
        )

        selected_single_level = "متوسط"

        if exam_type == "🎯 اختبار واحد (مستوى مخصص)":
            selected_single_level = st.selectbox(
                "اختر مستوى الاختبار:",
                ["سهل", "متوسط", "صعب"]
            )

        num_questions = st.number_input(
            "🔢 عدد الأسئلة:",
            min_value=3,
            max_value=50,
            value=10,
            step=1
        )

        max_hints = st.number_input(
            "💡 عدد فرص التلميحات المتاحة:",
            min_value=0,
            max_value=10,
            value=3,
            step=1
        )

        st.markdown("---")

        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

        st.markdown(
            "<div style='text-align: center; margin-top: 20px; font-size:0.85rem;'>"
            "<b>منصة الامتحانات الذكية</b><br>"
            "تطوير: <b>محمد عبدالله | Mohamed Abdallah</b></div>",
            unsafe_allow_html=True
        )

    # --- العنوان الرئيسي ---
    st.markdown(
        "<div class='main-header'>🎓 منصة الامتحانات والتحليل الذكي</div>",
        unsafe_allow_html=True
    )

    # تبويبات المنصة
    tab_exam, tab_chat = st.tabs([
        "📝 ملفات المادة والامتحانات الذكية",
        "🤖 الشات الذكي والمساعد للتحليل"
    ])

    # إنشاء عميل Gemini
    @st.cache_resource(show_spinner=False)
    def get_working_gemini_model(key):

        if not GEMINI_SUPPORT:
            raise RuntimeError(
                "مكتبة google-genai غير مثبتة. "
                "أضف google-genai إلى requirements.txt ثم أعد نشر التطبيق."
            )

        return genai.Client(api_key=key)

    # النموذج المختار من القائمة الجانبية
    GEMINI_MODEL = model_choices[selected_model_label]

    FAST_GENERATION_CONFIG = {
        "thinking_level": "low"
    }

    def _interaction_text(
        client,
        prompt,
        generation_config=None,
        max_output_tokens=2048
    ):

        config = dict(FAST_GENERATION_CONFIG)

        if generation_config:
            config.update(generation_config)

        config.setdefault("max_output_tokens", max_output_tokens)

        result = client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt,
            generation_config=config,
            store=False,
        )

        output = getattr(result, "output_text", None)

        if not output:
            raise ValueError(
                "لم يُرجع Gemini نصاً؛ قد تكون الاستجابة فارغة أو محجوبة."
            )

        return output.strip()

    def _stream_chat_answer(client, prompt):

        stream = client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt,
            generation_config={
                **FAST_GENERATION_CONFIG,
                "max_output_tokens": 2048
            },
            store=False,
            stream=True,
        )

        for event in stream:

            if getattr(event, "event_type", None) == "step.delta":

                delta = getattr(event, "delta", None)

                if getattr(delta, "type", None) == "text":

                    chunk = getattr(delta, "text", "")

                    if chunk:
                        yield chunk

    # استخراج النص من PDF
    def extract_text_from_pdf(uploaded_file, api_key=None):

        pdf_bytes = uploaded_file.getvalue()
        text = ""

        try:
            from io import BytesIO

            reader = pypdf.PdfReader(BytesIO(pdf_bytes))

            pages_text = [
                page.extract_text() or ""
                for page in reader.pages
            ]

            text = "\n".join(pages_text).strip()

        except Exception as e:
            st.warning(
                f"تعذر استخراج النص بالطريقة التقليدية: {e}"
            )

        if len(text) >= 80:
            return text

        if not api_key:
            raise ValueError(
                "الملف لا يحتوي على نص قابل للاستخراج. "
                "أدخل مفتاح Gemini لقراءة PDF المصوّر."
            )

        if len(pdf_bytes) > 20 * 1024 * 1024:
            raise ValueError(
                "حجم ملف PDF أكبر من 20 ميجابايت. "
                "قلّل حجمه أو قسّمه إلى ملفات أصغر."
            )

        temp_path = None

        try:

            client = get_working_gemini_model(api_key)

            st.info(
                "📷 الملف يبدو ممسوحاً ضوئياً؛ "
                "يتم رفعه إلى Gemini وقراءة صفحاته تلقائياً..."
            )

            with tempfile.NamedTemporaryFile(
                suffix=".pdf",
                delete=False
            ) as temp_file:

                temp_file.write(pdf_bytes)
                temp_path = temp_file.name

            uploaded = client.files.upload(
                file=Path(temp_path)
            )

            file_info = uploaded

            for _ in range(30):

                state = str(
                    getattr(file_info, "state", "")
                ).upper()

                if "ACTIVE" in state or not state:
                    break

                if "FAILED" in state:
                    raise RuntimeError(
                        "فشل Gemini في معالجة ملف PDF المرفوع."
                    )

                time.sleep(1)

                file_info = client.files.get(
                    name=uploaded.name
                )

            prompt = """
اقرأ ملف PDF المرفق صفحةً صفحة، واستخرج محتواه التعليمي
بما في ذلك النصوص العربية والإنجليزية والعناوين والتعريفات
والقوانين والمعادلات والجداول والرموز.

حافظ على ترتيب الصفحات، ولا تلخص ولا تخترع نصاً غير واضح.
ضع [غير واضح] عند تعذر القراءة.

أعد النص المستخرج فقط مع فاصل واضح بين الصفحات.
"""

            interaction = client.interactions.create(
                model=GEMINI_MODEL,
                input=[
                    {
                        "type": "document",
                        "uri": uploaded.uri,
                        "mime_type": "application/pdf"
                    },
                    {
                        "type": "text",
                        "text": prompt
                    },
                ],
            )

            scanned_text = (
                getattr(interaction, "output_text", None) or ""
            ).strip()

            if len(scanned_text) < 40:
                raise ValueError(
                    "لم يتمكن Gemini من قراءة نص كافٍ من صفحات الملف."
                )

            return scanned_text

        except Exception as e:

            raise RuntimeError(
                "تعذرت قراءة ملف PDF المصوّر عبر Gemini. "
                "تحقق من صلاحية المفتاح واتصال API ووضوح الملف. "
                "التفاصيل: " + str(e)
            ) from e

        finally:

            if temp_path:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except Exception:
                    pass
    # استخراج JSON من استجابة Gemini
    def _extract_json_payload(raw_text):

        if not raw_text:
            raise ValueError("أعاد Gemini استجابة فارغة.")

        cleaned = raw_text.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.I
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned
        )

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError:

            decoder = json.JSONDecoder()

            for pos, char in enumerate(cleaned):

                if char in "[{":

                    try:
                        value, _ = decoder.raw_decode(
                            cleaned[pos:]
                        )
                        return value

                    except json.JSONDecodeError:
                        continue

        raise ValueError(
            "لم تكن استجابة Gemini بصيغة JSON سليمة. أعد المحاولة."
        )

    # التأكد من صحة الأسئلة
    def _validate_questions(data, expected_count):

        if isinstance(data, dict):

            for key_name in ("questions", "quiz", "data"):

                if isinstance(data.get(key_name), list):
                    data = data[key_name]
                    break

        if not isinstance(data, list):
            raise ValueError(
                "تنسيق الأسئلة غير صحيح؛ المتوقع قائمة أسئلة."
            )

        valid = []

        for item in data:

            if not isinstance(item, dict):
                continue

            question = (
                item.get("q")
                or item.get("question")
                or item.get("question_text")
            )

            options = (
                item.get("options")
                or item.get("choices")
            )

            answer = (
                item.get("answer")
                or item.get("correct_answer")
            )

            if (
                not question
                or not isinstance(options, list)
                or len(options) < 2
                or not answer
            ):
                continue

            options = [
                str(option).strip()
                for option in options
                if str(option).strip()
            ]

            if len(options) < 2:
                continue

            answer = str(answer).strip()

            matched = next(
                (
                    option
                    for option in options
                    if option.strip() == answer
                ),
                None
            )

            if matched is None:

                matched = next(
                    (
                        option
                        for option in options
                        if option.startswith(answer[:2])
                        and answer[:2]
                    ),
                    None
                )

            if matched is None:
                continue

            valid.append({
                "q": str(question).strip(),
                "options": options,
                "answer": matched,
                "hint": str(
                    item.get("hint")
                    or "راجع الفكرة الأساسية المرتبطة بالسؤال."
                ),
                "explanation": str(
                    item.get("explanation")
                    or item.get("desc")
                    or "لا يتوفر شرح لهذا السؤال."
                ),
            })

        if len(valid) < expected_count:

            raise ValueError(
                f"تم استلام {len(valid)} سؤالًا صالحًا فقط "
                f"من أصل {expected_count}. "
                "لم يتم اعتماد الاختبار حتى لا يظهر ناقصًا؛ أعد المحاولة."
            )

        return valid[:expected_count]

    # اكتشاف أخطاء حدود الاستخدام
    def _is_rate_limit_error(exc):

        message = str(exc).lower()

        return any(token in message for token in (
            "429",
            "quota exceeded",
            "resourceexhausted",
            "rate limit",
            "too many requests"
        ))

    def _is_daily_quota_error(exc):

        message = str(exc).lower()

        return any(token in message for token in (
            "per_day",
            "perday",
            "requests_per_day",
            "daily quota",
            "per day quota",
            "limit: 0"
        ))

    # تحديد مدة الانتظار عند حدوث ضغط مؤقت
    def _retry_delay(exc, attempt):

        message = str(exc)

        match = re.search(
            r"(?:retry|wait)[^0-9]{0,30}(\d+(?:\.\d+)?)\s*s",
            message,
            re.I
        )

        if match:
            return min(
                max(float(match.group(1)) + 2, 5),
                90
            )

        return min(30 * (2 ** attempt), 90)

    # إرسال الطلب واستخراج JSON
    def _generate_json_with_retry(
        model,
        prompt,
        max_output_tokens=8192
    ):

        raw = _interaction_text(
            model,
            prompt,
            generation_config={
                "response_mime_type": "application/json"
            },
            max_output_tokens=max_output_tokens,
        )

        return _extract_json_payload(raw)

    # توليد اختبار واحد أو ثلاثة اختبارات
    def generate_quiz_with_ai(
        pdf_text,
        count,
        mode_type,
        level_name,
        key
    ):

        if not pdf_text or not pdf_text.strip():

            raise ValueError(
                "لم أتمكن من استخراج نص من ملف PDF. "
                "قد يكون الملف صوراً ممسوحة ضوئياً؛ "
                "استخدم ملف PDF يحتوي على نص قابل للتحديد."
            )

        model = get_working_gemini_model(key)

        # ==================================================
        # الإصلاح الأساسي:
        # إنشاء الاختبارات الثلاثة كل واحد بطلب مستقل
        # ==================================================
        if mode_type == "triple":

            st.info(
                "⏳ جاري إنشاء الاختبارات الثلاثة "
                "بالمستويات المختلفة..."
            )

            st.write("🟢 جاري إنشاء الاختبار السهل...")

            easy_quiz = generate_quiz_with_ai(
                pdf_text,
                count,
                "level",
                "سهل",
                key
            )

            st.success("✅ تم إنشاء الاختبار السهل.")

            st.write("🟡 جاري إنشاء الاختبار المتوسط...")

            medium_quiz = generate_quiz_with_ai(
                pdf_text,
                count,
                "level",
                "متوسط",
                key
            )

            st.success("✅ تم إنشاء الاختبار المتوسط.")

            st.write("🔴 جاري إنشاء الاختبار الصعب...")

            hard_quiz = generate_quiz_with_ai(
                pdf_text,
                count,
                "level",
                "صعب",
                key
            )

            st.success("✅ تم إنشاء الاختبار الصعب.")

            return {
                "سهل": easy_quiz,
                "متوسط": medium_quiz,
                "صعب": hard_quiz
            }

        seed = random.randint(1000, 999999)

        # إعداد نوع الأسئلة
        if mode_type == "laws":

            details = (
                "ركز على القوانين والتعريفات والمفاهيم "
                "والتطبيقات والمسائل الحسابية الواردة في المصدر."
            )

            title = "laws"

        elif mode_type == "comprehensive":

            details = (
                "غطِّ جميع أجزاء وفصول وموضوعات المصدر بتوازن."
            )

            title = "questions"

        else:

            details = (
                f"اجعل مستوى الأسئلة {level_name} تحديداً."
            )

            title = "questions"

        prompt = f"""
أنت واضع امتحانات متخصص في المنهج المصري.
اعتمد حصراً على محتوى المصدر:

<<<
{pdf_text[:14000]}
>>>

أنشئ {count} سؤال اختيار من متعدد جديدة.
{details}

أعد JSON فقط بالشكل:

{{
  "{title}": [
    {{
      "q": "السؤال",
      "options": [
        "أ) ...",
        "ب) ...",
        "ج) ...",
        "د) ..."
      ],
      "answer": "أ) ...",
      "hint": "تلميح لا يكشف الإجابة",
      "explanation": "شرح مختصر للإجابة في جملة أو جملتين"
    }}
  ]
}}

ضع {count} سؤالاً بالضبط،
واجعل answer مطابقاً حرفياً لأحد options.

اجعل الشرح مختصراً من جملة أو جملتين لتسريع التوليد.
استخدم LaTeX للمعادلات بين علامتي $ عند الحاجة.
معرف التنويع: {seed}.
"""

        output_limit = min(
            24000,
            max(4096, int(count) * 480)
        )

        payload = _generate_json_with_retry(
            model,
            prompt,
            max_output_tokens=output_limit
        )

        if isinstance(payload, dict):

            questions = (
                payload.get("questions")
                or payload.get("laws")
                or payload.get("data")
            )

            if questions is None:

                questions = next(
                    (
                        value
                        for value in payload.values()
                        if isinstance(value, list)
                    ),
                    None
                )

        else:
            questions = payload

        return _validate_questions(
            questions,
            count
        )

    # --- تبويب الاختبارات والتحليل ---
    with tab_exam:

        st.markdown(
            "<div class='sub-header'>"
            "ارفع ملف المادة أو ملف القوانين لإنشاء امتحانات ذكية، "
            "منظمة ومجهزة بالمعادلات الشاملة"
            "</div>",
            unsafe_allow_html=True
        )

        uploaded_file = st.file_uploader(
            "📂 قم برفع ملف الـ PDF (مادة شريحة / ملخص / قوانين):",
            type=["pdf"]
        )

        if uploaded_file is not None:

            if not PDF_SUPPORT or not GEMINI_SUPPORT:

                st.error(
                    "⚠️ يرجى التأكد من تثبيت المكتبات المطلوبة "
                    "(pypdf و google-genai)."
                )

            elif not api_key:

                st.warning(
                    "⚠️ يرجى كتابة مفتاح Gemini API Key "
                    "في القائمة الجانبية أولاً."
                )

            else:

                if st.button("✨ إرسال وإنشاء أسئلة اختبار جديدة"):

                    try:

                        with st.spinner(
                            "جاري تجهيز الملف وإنشاء الاختبار..."
                        ):

                            pdf_bytes = uploaded_file.getvalue()

                            pdf_fingerprint = hashlib.sha256(
                                pdf_bytes
                            ).hexdigest()

                            if (
                                st.session_state.get("pdf_fingerprint")
                                == pdf_fingerprint
                                and st.session_state.get("pdf_text")
                            ):

                                pdf_text_data = st.session_state.pdf_text

                            else:

                                pdf_text_data = extract_text_from_pdf(
                                    uploaded_file,
                                    api_key
                                )

                                st.session_state.pdf_text = pdf_text_data

                                st.session_state.pdf_fingerprint = (
                                    pdf_fingerprint
                                )

                            st.session_state.hints_used = 0
                            st.session_state.unlocked_hints = set()

                            if not pdf_text_data.strip():

                                raise ValueError(
                                    "ملف PDF لا يحتوي على نص قابل للاستخراج. "
                                    "إذا كان الملف صوراً ممسوحة ضوئياً "
                                    "فستحتاج إلى OCR أولاً."
                                )

                            if exam_type == "🔥 3 اختبارات (سهل، متوسط، صعب)":

                                st.session_state.quizzes = (
                                    generate_quiz_with_ai(
                                        pdf_text_data,
                                        int(num_questions),
                                        "triple",
                                        None,
                                        api_key
                                    )
                                )

                            elif exam_type == "🚀 اختبار شامل للمادة":

                                st.session_state.quizzes = {
                                    "اختبار شامل": generate_quiz_with_ai(
                                        pdf_text_data,
                                        int(num_questions),
                                        "comprehensive",
                                        None,
                                        api_key
                                    )
                                }

                            elif exam_type == "📐 اختبار قوانين وتطبيقات (من ملف القوانين)":

                                st.session_state.quizzes = {
                                    "اختبار القوانين والتطبيقات": generate_quiz_with_ai(
                                        pdf_text_data,
                                        int(num_questions),
                                        "laws",
                                        None,
                                        api_key
                                    )
                                }

                            else:

                                st.session_state.quizzes = {
                                    f"اختبار ({selected_single_level})": generate_quiz_with_ai(
                                        pdf_text_data,
                                        int(num_questions),
                                        "level",
                                        selected_single_level,
                                        api_key
                                    )
                                }

                            st.session_state.submitted_quiz = False
                            st.session_state.show_review_warning = False

                            st.success(
                                "✅ تم توليد الامتحان بنجاح "
                                "وصياغة الأسئلة والمعادلات!"
                            )

                    except Exception as e:

                        err_message = str(e)

                        if _is_rate_limit_error(e):

                            st.error(
                                "تعذر التوليد لأن حصة Gemini المتاحة "
                                "لهذا المفتاح انتهت مؤقتاً. "
                                "انتظر حتى تتجدد الحصة، أو تحقق من "
                                "Usage & Billing في Google AI Studio."
                            )

                        else:

                            st.error(
                                f"حدث خطأ أثناء التوليد: {err_message}"
                            )
        # عرض الامتحانات
        if (
            "quizzes" in st.session_state
            and st.session_state.quizzes
        ):

            st.markdown("---")

            quiz_keys = list(
                st.session_state.quizzes.keys()
            )

            if len(quiz_keys) > 1:

                tabs_list = st.tabs([
                    f"📌 {key}"
                    for key in quiz_keys
                ])

            else:

                tabs_list = [st.container()]

            for idx, tab_item in enumerate(tabs_list):

                current_key = quiz_keys[idx]

                with tab_item:

                    quiz_data = st.session_state.quizzes[
                        current_key
                    ]

                    st.markdown(
                        f"""
                        <div style='display:flex;
                        justify-content:space-between;
                        align-items:center;'>
                        <h4>📝 {current_key} -
                        عدد الأسئلة: {len(quiz_data)}</h4>
                        <span>المتبقي من فرص التلميحات:
                        <b>{max(0, max_hints - st.session_state.hints_used)}</b>
                        / {max_hints}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.markdown("---")

                    user_answers = {}

                    for i, q_item in enumerate(quiz_data):

                        question_text = (
                            q_item.get("q")
                            or q_item.get("question")
                            or q_item.get("question_text")
                            or f"السؤال رقم {i+1} (تعذر العثور على النص)"
                        )

                        st.markdown(
                            "<div class='bright-card'>",
                            unsafe_allow_html=True
                        )

                        st.markdown(
                            f"##### ❓ السؤال {i+1}:"
                        )

                        st.write(question_text)

                        hint_key = f"{current_key}_{i}"

                        show_hint_btn = st.checkbox(
                            "💡 إظهار التلميحة (تستهلك 1 من الفرص)",
                            key=f"chk_hint_{hint_key}"
                        )

                        if show_hint_btn:

                            if hint_key not in st.session_state.unlocked_hints:

                                if st.session_state.hints_used < max_hints:

                                    st.session_state.hints_used += 1

                                    st.session_state.unlocked_hints.add(
                                        hint_key
                                    )

                                else:

                                    st.warning(
                                        "⚠️ لقد استنفدت جميع فرص "
                                        "فتح التلميحات لهذا الاختبار!"
                                    )

                            if hint_key in st.session_state.unlocked_hints:

                                st.info(
                                    f"💡 **تلميح:** "
                                    f"{q_item.get('hint', 'لا يوجد تلميح متوفر.')}"
                                )

                        options_list = (
                            q_item.get("options")
                            or q_item.get("choices")
                            or ["أ) -", "ب) -", "ج) -", "د) -"]
                        )

                        selected_opt = st.radio(
                            label=f"اختر الإجابة الصحيحة للسؤال {i+1}:",
                            options=["-- اختر إجابة --"] + options_list,
                            key=f"rad_{current_key}_{i}"
                        )

                        user_answers[i] = (
                            None
                            if selected_opt == "-- اختر إجابة --"
                            else selected_opt
                        )

                        # العلامة المائية داخل كارت الامتحان
                        st.markdown(
                            "<div class='exam-watermark'>"
                            "محمد عبدالله - Mohamed Abdallah"
                            "</div>",
                            unsafe_allow_html=True
                        )

                        st.markdown(
                            "</div>",
                            unsafe_allow_html=True
                        )

                    if st.button(
                        f"📩 إرسال وتصحيح الاختبار النهائي ({current_key})",
                        key=f"btn_submit_{current_key}"
                    ):

                        st.session_state.current_active_level = (
                            current_key
                        )

                        st.session_state.temp_user_answers = (
                            user_answers
                        )

                        st.session_state.show_review_warning = True

            # تأكيد تسليم الاختبار
            if st.session_state.get(
                "show_review_warning",
                False
            ):

                st.warning(
                    "⚠️ عزيزي الطالب: راجع إجاباتك جيداً "
                    "للتحقق قبل تسليم الاختبار بشكل نهائي!"
                )

                c_btn1, c_btn2 = st.columns(2)

                with c_btn1:

                    if st.button(
                        "🔍 العودة للمراجعة",
                        key="back_review"
                    ):

                        st.session_state.show_review_warning = False
                        st.rerun()

                with c_btn2:

                    if st.button(
                        "✅ تأكيد التسليم الآن",
                        key="confirm_submit"
                    ):

                        st.session_state.submitted_quiz = True

                        st.session_state.submitted_level = (
                            st.session_state.current_active_level
                        )

                        st.session_state.user_answers = (
                            st.session_state.temp_user_answers
                        )

                        st.session_state.show_review_warning = False

                        st.rerun()

            # عرض النتيجة النهائية
            if st.session_state.get(
                "submitted_quiz",
                False
            ):

                active_key = st.session_state.submitted_level

                quiz = st.session_state.quizzes[active_key]

                score = 0
                total = len(quiz)

                st.markdown(
                    "<div class='bright-card'>",
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"### 📊 النتيجة التفصيلية لاختبار: ({active_key})"
                )

                for i, q_data in enumerate(quiz):

                    correct_ans = (
                        q_data.get("answer")
                        or q_data.get("correct_answer")
                    )

                    user_ans = st.session_state.user_answers.get(i)

                    if user_ans == correct_ans:

                        score += 1

                        st.success(
                            f"✔️ **السؤال {i+1}: إجابة صحيحة!**"
                        )

                    else:

                        st.error(
                            f"❌ **السؤال {i+1}: إجابة غير صحيحة**"
                        )

                        st.write(
                            f"- **إجابتك:** "
                            f"{user_ans if user_ans else 'لم تقم بالإجابة'}"
                        )

                        st.write(
                            f"- **الإجابة النموذجية:** {correct_ans}"
                        )

                    explanation_text = (
                        q_data.get("explanation")
                        or q_data.get("desc")
                    )

                    if explanation_text:

                        st.info(
                            f"💡 **الشرح والتفسير:** {explanation_text}"
                        )

                    st.markdown("---")

                perc = (score / total) * 100

                st.metric(
                    "النتيجة النهائية",
                    f"{score} / {total}",
                    f"{perc:.1f}%"
                )

                if perc >= 85:

                    st.balloons()

                    st.success(
                        "🎉 أداء ممتاز وشامل! استمر في هذا التفوق."
                    )

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )

    # --- تبويب الشات الذكي والتحليل التفاعلي ---
    with tab_chat:

        st.markdown(
            "<div class='sub-header'>"
            "تحدث مع الذكاء الاصطناعي لتحليل أي جزء من المادة "
            "أو طرح الأسئلة والقوانين والمعادلات"
            "</div>",
            unsafe_allow_html=True
        )

        if "pdf_text" not in st.session_state:

            st.info(
                "💡 قم برفع ملف الـ PDF في التبويب الأول أولاً، "
                "ثم يمكنك إجراء دردشة وتحليل تفاعلي "
                "مع الذكاء الاصطناعي حول محتواه."
            )

        elif not api_key:

            st.warning(
                "⚠️ يرجى إدخال مفتاح Gemini API Key "
                "في القائمة الجانبية لتفعيل الشات."
            )

        else:

            for chat in st.session_state.chat_history:

                st.markdown(
                    f"**👤 أنت:** {chat['user']}"
                )

                st.markdown(
                    f"**🤖 المساعد الذكي:** {chat['assistant']}"
                )

                st.markdown("---")

            # نموذج إرسال الأسئلة إلى الشات
            with st.form(
                key="chat_form",
                clear_on_submit=True
            ):

                user_query = st.text_input(
                    "اسأل الذكاء الاصطناعي عن أي جزء في المادة، "
                    "القوانين، أو المسائل..."
                )

                submit_chat = st.form_submit_button(
                    "إرسال السؤال 🚀"
                )

                if submit_chat and user_query.strip():

                    with st.spinner(
                        "جاري التحليل والإجابة بسرعة..."
                    ):

                        try:

                            model = get_working_gemini_model(
                                api_key
                            )

                            chat_prompt = f"""
أنت معلم ثانوية عامة ومساعد محترف.

بناءً على نص المادة المستخرج التالي:

---
{st.session_state.pdf_text[:10000]}
---

أجب على سؤال الطالب بكل دقة ووضوح وبنظام منظم.

اعتمد على محتوى الملف في الإجابة.
إذا لم تجد المعلومة في الملف، وضّح ذلك للطالب.
استخدم صياغة LaTeX في المعادلات إن وجدت.

سؤال الطالب:
{user_query}
"""

                            ans_text = st.write_stream(
                                _stream_chat_answer(
                                    model,
                                    chat_prompt
                                )
                            )

                            if not ans_text:

                                raise ValueError(
                                    "لم تصل إجابة من Gemini."
                                )

                            st.session_state.chat_history.append({
                                "user": user_query,
                                "assistant": ans_text
                            })

                            st.rerun()

                        except Exception as e:

                            st.error(
                                "حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: "
                                f"{e}"
                            )
