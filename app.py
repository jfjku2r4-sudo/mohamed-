import streamlit as st
import json
import re
import random
import time

# محاولة استيراد مكتبة قراءة ملفات الـ PDF واستخراج النص منها
try:
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    try:
        import PyPDF2 as pypdf
        PDF_SUPPORT = True
    except ImportError:
        PDF_SUPPORT = False

# استيراد مكتبة الذكاء الاصطناعي Gemini
try:
    import google.generativeai as genai
    GEMINI_SUPPORT = True
except ImportError:
    GEMINI_SUPPORT = False

# إعدادات الصفحة
st.set_page_config(
    page_title="منصة امتحانات الثانوية العامة الذكية | Mohamed Abdallah",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم الواجهة بـ CSS يدعم الوضعين الفاتح والغامق تلقائياً بمرونة تامة
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

    /* كروت الامتحانات بتصميم متكيف ديناميكياً مع الوضع الفاتح والغامق */
    .bright-card {
        padding: 25px;
        border-radius: 18px;
        border: 2px solid rgba(59, 130, 246, 0.2);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
        position: relative;
    }

    /* العلامة المائية المحصورة فقط داخل كارت الامتحان */
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

# إدارة حالة الجلسة والتسجيل
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
    st.markdown("<div class='main-header'>🔐 بوابة الدخول للمنصة الذكية</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>قم بتسجيل الدخول للوصول لكافة الامتحانات والشات الذكي وتحليل الملفات والقوانين</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='bright-card'>", unsafe_allow_html=True)
        with st.form("login_form"):
            input_name = st.text_input("👤 اسم الطالب الثلاثي", placeholder="اكتب اسمك الثلاثي...")
            password = st.text_input("🔑 كلمة المرور", type="password", placeholder="أدخل كلمة المرور...")
            remember_me = st.checkbox("حفظ الجلسة والتسجيل في هذا المتصفح", value=True)
            submit_login = st.form_submit_button("دخول المنصة 🚀")
            
            if submit_login:
                if password == "01224982634" and input_name.strip() != "":
                    st.session_state.logged_in = True
                    st.session_state.username = input_name.strip()
                    st.success(f"✨ أهلاً بك يا {st.session_state.username}! جاري فتح المنصة...")
                    st.rerun()
                elif password != "01224982634":
                    st.error("❌ كلمة المرور غير صحيحة.")
                else:
                    st.warning("⚠️ يرجى كتابة اسمك الثلاثي أولاً.")
        st.markdown("</div>", unsafe_allow_html=True)
                    
    st.markdown("<div class='footer'>حقوق الملكية والتطوير محفوظة © <b>محمد عبدالله - Mohamed Abdallah</b> 💻</div>", unsafe_allow_html=True)

else:
    # --- القائمة الجانبية ---
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=100)
        st.markdown(f"### 👤 الطالب: **{st.session_state.username}**")
        st.markdown("---")
        
        st.header("⚙️ إعدادات النموذج والاختبار")
        api_key = st.text_input("🔑 مفتاح Gemini API Key:", type="password", help="أدخل مفتاح Google Gemini API")
        
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
            selected_single_level = st.selectbox("اختر مستوى الاختبار:", ["سهل", "متوسط", "صعب"])

        num_questions = st.number_input("🔢 عدد الأسئلة:", min_value=3, max_value=50, value=10, step=1)
        max_hints = st.number_input("💡 عدد فرص التلميحات المتاحة:", min_value=0, max_value=10, value=3, step=1)
        
        st.markdown("---")
        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
            
        st.markdown("<div style='text-align: center; margin-top: 20px; font-size:0.85rem;'><b>منصة الامتحانات الذكية</b><br>تطوير: <b>محمد عبدالله | Mohamed Abdallah</b></div>", unsafe_allow_html=True)

    # --- العنوان الرئيسي ---
    st.markdown("<div class='main-header'>🎓 منصة الامتحانات والتحليل الذكي</div>", unsafe_allow_html=True)

    # تبويبات المنصة (التحليل والاختبارات + الشات الذكي مع AI)
    tab_exam, tab_chat = st.tabs(["📝 ملفات المادة والامتحانات الذكية", "🤖 الشات الذكي والمساعد للتحليل"])

    # دالة استخراج النص من ملف الـ PDF لتخفيف الحجم تماماً على الـ API
    def extract_text_from_pdf(uploaded_file):
        text = ""
        try:
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            st.error(f"خطأ في قراءة ملف الـ PDF: {e}")
        return text

    # دالة اختيار النموذج المدعوم والحديث مع Fallbacks آمنة
    def get_working_gemini_model(key):
        genai.configure(api_key=key)
        fallback_models = ['gemini-3.8-flash', 'gemini-2.5-flash', 'gemini-pro']
        
        for f_model in fallback_models:
            try:
                model = genai.GenerativeModel(f_model)
                return model
            except Exception:
                continue
                
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    return genai.GenerativeModel(m.name)
        except Exception:
            pass
            
        raise Exception("لم يتم العثور على أي نموذج مدعوم في مفتاح API هذا. تأكد من صحة المفتاح.")

    # دالة التوليد التفاعلي عبر Gemini مع إجبار النموذج على إخراج JSON صالح 100%
    def generate_quiz_with_ai(pdf_text, count, mode_type, level_name, key):
        model = get_working_gemini_model(key)
        random_seed = random.randint(1000, 999999)

        prompt_details = ""
        if mode_type == "laws":
            prompt_details = "استخرج القوانين والمفاهيم العلمية والرياضية الواردة بالنص وصغ أسئلة وتطبيقات مسائل وحسابات ومعادلات عليها بدقة."
        elif mode_type == "comprehensive":
            prompt_details = "صغ اختباراً شاملاً يغطي كافة أجزاء وفصول وموضوعات النص بشكل متوازن ومتدرج."
        else:
            prompt_details = f"صغ الأسئلة بمستوى ({level_name}) تحديداً."

        prompt = f"""
        أنت خبير واضع امتحانات الثانوية العامة المصرية والجامعات.
        قم بقراءة النص المستخرج من المنهج بدقة:
        ---
        {pdf_text[:12000]}
        ---
        أنشئ {count} أسئلة اختيارات من متعدد (MCQ) جديدة تماماً وفريدة (معرف التوليد: {random_seed}).
        تفاصيل التوليد: {prompt_details}

        شروط ومعايير التنسيق الصارمة:
        1. إذا كانت المادة تحتوي على معادلات رياضية أو كيميائية أو فيزيائية، اكتبها بنص LaTeX واضح بين علامتي $ (مثال: $E = mc^2$ أو $\\int_{{0}}^{{\\infty}} f(x)dx$).
        2. الإجابات يجب أن تكون واضحة ومحددة.
        3. لكل سؤال أضف تلميحاً مساعداً (hint) لا يكشف الحل مباشرة.
        4. أضف شرحاً تفصيلياً ممتازاً لسبب الإجابة الصحيحة.
        5. يجب أن تكون الاستجابة بصيغة JSON صحيحة ومتوافقة تماماً مع المعيار (Array of Objects) بدون أي نصوص أو تعليقات خارجية.
        """

        max_retries = 3
        delay = 8

        for attempt in range(max_retries):
            try:
                # استخدام إعدادات التوليد لفرض صيغة JSON وتجنب أي خطأ في التحليل
                generation_config = {"response_mime_type": "application/json"}
                response = model.generate_content(prompt, generation_config=generation_config)
                raw_text = response.text.strip()
                
                match = re.search(r'\[\s*\{.*\}\s*\]', raw_text, re.DOTALL)
                if match:
                    clean_json_str = match.group(0)
                else:
                    clean_json_str = raw_text.replace("```json", "").replace("```", "").strip()
                    
                return json.loads(clean_json_str)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "Quota exceeded" in err_str:
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))
                        continue
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)

    # --- تبويب الاختبارات والتحليل ---
    with tab_exam:
        st.markdown("<div class='sub-header'>ارفع ملف المادة أو ملف القوانين لإنشاء امتحانات ذكية، منظمة ومجهزة بالمعادلات الشاملة</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("📂 قم برفع ملف الـ PDF (مادة شريحة / ملخص / قوانين):", type=["pdf"])

        if uploaded_file is not None:
            if not PDF_SUPPORT or not GEMINI_SUPPORT:
                st.error("⚠️ يرجى التأكد من تثبيت المكتبات المطلوبة (pypdf و google-generativeai).")
            elif not api_key:
                st.warning("⚠️ يرجى كتابة مفتاح Gemini API Key في القائمة الجانبية أولاً.")
            else:
                if st.button("✨ إرسال وإنشاء أسئلة اختبار جديدة"):
                    try:
                        with st.spinner("جاري استخراج النصوص وتحليل المحتوى بالذكاء الاصطناعي..."):
                            pdf_text_data = extract_text_from_pdf(uploaded_file)
                            st.session_state.pdf_text = pdf_text_data
                            
                            st.session_state.hints_used = 0
                            st.session_state.unlocked_hints = set()

                            if exam_type == "🔥 3 اختبارات (سهل، متوسط، صعب)":
                                q_easy = generate_quiz_with_ai(pdf_text_data, num_questions, "level", "سهل", api_key)
                                time.sleep(5)
                                q_med = generate_quiz_with_ai(pdf_text_data, num_questions, "level", "متوسط", api_key)
                                time.sleep(5)
                                q_hard = generate_quiz_with_ai(pdf_text_data, num_questions, "level", "صعب", api_key)
                                
                                st.session_state.quizzes = {
                                    "سهل": q_easy,
                                    "متوسط": q_med,
                                    "صعب": q_hard
                                }
                            elif exam_type == "🚀 اختبار شامل للمادة":
                                st.session_state.quizzes = {
                                    "اختبار شامل": generate_quiz_with_ai(pdf_text_data, num_questions, "comprehensive", None, api_key)
                                }
                            elif exam_type == "📐 اختبار قوانين وتطبيقات (من ملف القوانين)":
                                st.session_state.quizzes = {
                                    "اختبار القوانين والتطبيقات": generate_quiz_with_ai(pdf_text_data, num_questions, "laws", None, api_key)
                                }
                            else:
                                st.session_state.quizzes = {
                                    f"اختبار ({selected_single_level})": generate_quiz_with_ai(pdf_text_data, num_questions, "level", selected_single_level, api_key)
                                }
                                
                            st.session_state.submitted_quiz = False
                            st.session_state.show_review_warning = False
                            st.success("✅ تم توليد الامتحان بنجاح وصياغة الأسئلة والمعادلات!")
                    except Exception as e:
                        err_message = str(e)
                        if "429" in err_message or "Quota exceeded" in err_message:
                            st.error("⚠️ **تم استنفاد حدود الطلبات المؤقتة (Rate Limit).**\n\n"
                                     "💡 **نصيحة هامة:** اختر **'اختبار واحد (مستوى مخصص)'** أو انتظر دقيقة ثم حاول مرة أخرى.")
                        else:
                            st.error(f"حدث خطأ أثناء التوليد: {e}")

        # عرض الامتحانات
        if "quizzes" in st.session_state and st.session_state.quizzes:
            st.markdown("---")
            
            quiz_keys = list(st.session_state.quizzes.keys())
            if len(quiz_keys) > 1:
                tabs_list = st.tabs([f"📌 {k}" for k in quiz_keys])
            else:
                tabs_list = [st.container()]

            for idx, tab_item in enumerate(tabs_list):
                current_key = quiz_keys[idx]
                with tab_item:
                    quiz_data = st.session_state.quizzes[current_key]
                    
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center;'><h4>📝 {current_key} - عدد الأسئلة: {len(quiz_data)}</h4><span>المتبقي من فرص التلميحات: <b>{max(0, max_hints - st.session_state.hints_used)}</b> / {max_hints}</span></div>", unsafe_allow_html=True)
                    st.markdown("---")

                    user_answers = {}
                    for i, q_item in enumerate(quiz_data):
                        st.markdown(f"<div class='bright-card'>", unsafe_allow_html=True)
                        st.markdown(f"##### ❓ السؤال {i+1}:")
                        st.write(q_item['q'])
                        
                        hint_key = f"{current_key}_{i}"
                        show_hint_btn = st.checkbox(f"💡 إظهار التلميحة (تستهلك 1 من الفرص)", key=f"chk_hint_{hint_key}")
                        
                        if show_hint_btn:
                            if hint_key not in st.session_state.unlocked_hints:
                                if st.session_state.hints_used < max_hints:
                                    st.session_state.hints_used += 1
                                    st.session_state.unlocked_hints.add(hint_key)
                                else:
                                    st.warning("⚠️ لقد استنفدت جميع فرص فتح التلميحات لهذا الاختبار!")
                            
                            if hint_key in st.session_state.unlocked_hints:
                                st.info(f"💡 **تلميح:** {q_item.get('hint', 'لا يوجد تلميح متوفر.')}")

                        selected_opt = st.radio(
                            label=f"اختر الإجابة الصحيحة للسؤال {i+1}:",
                            options=["-- اختر إجابة --"] + q_item['options'],
                            key=f"rad_{current_key}_{i}"
                        )
                        user_answers[i] = None if selected_opt == "-- اختر إجابة --" else selected_opt
                        
                        # العلامة المائية المحصورة في كارت الامتحان فقط
                        st.markdown("<div class='exam-watermark'>محمد عبدالله - Mohamed Abdallah</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    if st.button(f"📩 إرسال وتصحيح الاختبار النهائي ({current_key})", key=f"btn_submit_{current_key}"):
                        st.session_state.current_active_level = current_key
                        st.session_state.temp_user_answers = user_answers
                        st.session_state.show_review_warning = True

            if st.session_state.get("show_review_warning", False):
                st.warning("⚠️ عزيزي الطالب: راجع إجاباتك جيداً للتحقق قبل تسليم الاختبار بشكل نهائي!")
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("🔍 العودة للمراجعة", key="back_review"):
                        st.session_state.show_review_warning = False
                        st.rerun()
                with c_btn2:
                    if st.button("✅ تأكيد التسليم الآن", key="confirm_submit"):
                        st.session_state.submitted_quiz = True
                        st.session_state.submitted_level = st.session_state.current_active_level
                        st.session_state.user_answers = st.session_state.temp_user_answers
                        st.session_state.show_review_warning = False
                        st.rerun()

            if st.session_state.get("submitted_quiz", False):
                active_key = st.session_state.submitted_level
                quiz = st.session_state.quizzes[active_key]
                score = 0
                total = len(quiz)
                
                st.markdown("<div class='bright-card'>", unsafe_allow_html=True)
                st.markdown(f"### 📊 النتيجة التفصيلية لاختبار: ({active_key})")
                
                for i, q_data in enumerate(quiz):
                    correct_ans = q_data['answer']
                    user_ans = st.session_state.user_answers.get(i)
                    
                    if user_ans == correct_ans:
                        score += 1
                        st.success(f"✔️ **السؤال {i+1}: إجابة صحيحة!**")
                    else:
                        st.error(f"❌ **السؤال {i+1}: إجابة غير صحيحة**")
                        st.write(f"- **إجابتك:** {user_ans if user_ans else 'لم تقم بالإجابة'}")
                        st.write(f"- **الإجابة النموذجية:** {correct_ans}")
                    
                    if "explanation" in q_data:
                        st.info(f"💡 **الشرح والتفسير:** {q_data['explanation']}")
                    st.markdown("---")
                
                perc = (score / total) * 100
                st.metric("النتيجة النهائية", f"{score} / {total}", f"{perc:.1f}%")
                if perc >= 85:
                    st.balloons()
                    st.success("🎉 أداء ممتاز وشامل! استمر في هذا التفوق.")
                st.markdown("</div>", unsafe_allow_html=True)

    # --- تبويب الشات الذكي والتحليل التفاعلي ---
    with tab_chat:
        st.markdown("<div class='sub-header'>تحدث مع الذكاء الاصطناعي لتحليل أي جزء من المادة أو طرح الأسئلة والقوانين والمعادلات</div>", unsafe_allow_html=True)

        if "pdf_text" not in st.session_state:
            st.info("💡 قم برفع ملف الـ PDF في التبويب الأول أولاً، ثم يمكنك إجراء دردشة وتحليل تفاعلي مع الذكاء الاصطناعي حول محتواه.")
        elif not api_key:
            st.warning("⚠️ يرجى إدخال مفتاح Gemini API Key في القائمة الجانبية لتفعيل الشات.")
        else:
            for chat in st.session_state.chat_history:
                st.markdown(f"**👤 أنت:** {chat['user']}")
                st.markdown(f"**🤖 المساعد الذكي:** {chat['assistant']}")
                st.markdown("---")

            with st.form(key="chat_form", clear_on_submit=True):
                user_query = st.text_input("اسأل الذكاء الاصطناعي عن أي جزء في المادة، القوانين، أو المسائل...")
                submit_chat = st.form_submit_button("إرسال السؤال 🚀")

                if submit_chat and user_query.strip():
                    with st.spinner("جاري التحليل والإجابة بسرعة..."):
                        try:
                            model = get_working_gemini_model(api_key)
                            chat_prompt = f"""
                            أنت معلم وثانوية عامة ومساعد محترف.
                            بناءً على نص المادة المستخرج التالي:
                            ---
                            {st.session_state.pdf_text[:10000]}
                            ---
                            أجب على سؤال الطالب بكل دقة ووضوح وبنظام منظم.
                            استخدم صياغة LaTeX في المعادلة إن وجدت.
                            سؤال الطالب: {user_query}
                            """
                            
                            chat_response = model.generate_content(chat_prompt)
                            ans_text = chat_response.text
                            
                            st.session_state.chat_history.append({"user": user_query, "assistant": ans_text})
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {e}")
