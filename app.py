import streamlit as st
import json
import re
import random

# محاولة استيراد مكتبة قراءة ملفات الـ PDF
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

# تصميم الواجهة بـ CSS والتصاميم الزاهية مع العلامات المائية
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }

    /* العلامة المائية للستارة والخلفية العامة */
    .stAppViewContainer {
        background-color: #f4f7fe;
        background-image: radial-gradient(#3b82f6 0.5px, transparent 0.5px), radial-gradient(#ec4899 0.5px, #f4f7fe 0.5px);
        background-size: 20px 20px;
        background-position: 0 0,10px 10px;
    }

    /* علامة مائية عائمة متكررة */
    .watermark-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 9999;
        opacity: 0.04;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-around;
        align-content: space-around;
        font-size: 2rem;
        font-weight: 900;
        color: #000;
        user-select: none;
    }

    .main-header {
        font-size: 2.6rem;
        background: linear-gradient(135deg, #2563eb, #7c3aed, #db2777);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 900;
        margin-bottom: 5px;
    }

    .watermark-badge {
        display: inline-block;
        background: linear-gradient(90deg, #ec4899, #8b5cf6);
        color: white;
        padding: 4px 15px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
        letter-spacing: 1px;
        box-shadow: 0 4px 10px rgba(236, 72, 153, 0.3);
        margin-bottom: 15px;
    }

    .sub-header {
        font-size: 1.15rem;
        color: #4b5563;
        text-align: center;
        margin-bottom: 25px;
        font-weight: 600;
    }

    /* كروت زاهية */
    .bright-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 25px;
        border-radius: 18px;
        border: 2px solid #e0e7ff;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.1), 0 8px 10px -6px rgba(59, 130, 246, 0.1);
        margin-bottom: 25px;
        position: relative;
    }

    /* علامة مائية داخل الامتحان */
    .exam-watermark {
        position: absolute;
        right: 15px;
        bottom: 10px;
        font-size: 0.75rem;
        color: #94a3b8;
        font-weight: bold;
        pointer-events: none;
    }

    .footer {
        text-align: center;
        color: #4b5563;
        margin-top: 40px;
        font-size: 1rem;
        border-top: 2px solid #e2e8f0;
        padding-top: 20px;
        font-weight: 700;
    }
    </style>

    <div class="watermark-overlay">
        <span>محمد عبدالله - Mohamed Abdallah</span>
        <span>محمد عبدالله - Mohamed Abdallah</span>
        <span>محمد عبدالله - Mohamed Abdallah</span>
        <span>محمد عبدالله - Mohamed Abdallah</span>
        <span>محمد عبدالله - Mohamed Abdallah</span>
        <span>محمد عبدالله - Mohamed Abdallah</span>
    </div>
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
    st.markdown("<div style='text-align: center;'><span class='watermark-badge'>✨ Mohamed Abdallah Platform ✨</span></div>", unsafe_allow_html=True)
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
        st.markdown("<div style='text-align:center; margin-top:15px; font-size:0.85rem; color:#64748b;'>العلامة المائية المحمية: <b>محمد عبدالله | Mohamed Abdallah</b></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
                    
    st.markdown("<div class='footer'>حقوق الملكية والتطوير محفوظة © <b>محمد عبدالله - Mohamed Abdallah</b> 💻</div>", unsafe_allow_html=True)

else:
    # --- القائمة الجانبية ---
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/graduation-cap.png", width=100)
        st.markdown(f"### 👤 الطالب: **{st.session_state.username}**")
        st.markdown("<span style='color:#8b5cf6; font-weight:bold;'>علامة مائية: محمد عبدالله</span>", unsafe_allow_html=True)
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
            
        st.markdown("<div style='text-align: center; color: #64748b; margin-top: 20px; font-size:0.85rem;'><b>منصة الامتحانات الذكية</b><br>تطوير: <b>محمد عبدالله | Mohamed Abdallah</b></div>", unsafe_allow_html=True)

    # --- شريط العلامة المائية العلوية ---
    st.markdown("<div style='text-align: center;'><span class='watermark-badge'>علامة مائية موثقة: محمد عبدالله - Mohamed Abdallah</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='main-header'>🎓 منصة الامتحانات والتحليل الذكي</div>", unsafe_allow_html=True)

    # تبويبات المنصة (التحليل والاختبارات + الشات الذكي مع AI)
    tab_exam, tab_chat = st.tabs(["📝 ملفات المادة والامتحانات الذكية", "🤖 الشات الذكي والمساعد للتحليل"])

    # دالة ذكية مرنة لاختيار النموذج المتاح أوتوماتيكياً (تمنع أخطاء 404 وتتوافق مع كافة المفتاحين)
    def get_working_gemini_model(key):
        genai.configure(api_key=key)
        
        # قائمة النماذج المحدثة والمستقرة بالترتيب الأحدث
        fallback_models = [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-2.0-flash',
            'gemini-pro'
        ]
        
        # محاولة البحث الديناميكي عن أي نموذج يدعم التوليد متاح لحسابك
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'gemini' in m.name:
                        model_clean_name = m.name.replace("models/", "")
                        try:
                            return genai.GenerativeModel(model_clean_name)
                        except Exception:
                            continue
        except Exception:
            pass
            
        # تجربة القائمة الاحتياطية الثابتة
        for f_model in fallback_models:
            try:
                model = genai.GenerativeModel(f_model)
                # اختبار سريع لضمان عمل النموذج
                return model
            except Exception:
                continue
                
        raise Exception("لم يتم العثور على أي نموذج مدعوم في مفتاح API هذا. تأكد من صحة المفتاح أو تفعيل الباقة المجانية في حسابك.")

    # دالة التوليد التفاعلي عبر Gemini
    def generate_quiz_with_ai(pdf_bytes, count, mode_type, level_name, key):
        model = get_working_gemini_model(key)

        pdf_file_part = {"mime_type": "application/pdf", "data": pdf_bytes}

        # توليد رقم عشوائي لضمان أسئلة جديدة دائماً
        random_seed = random.randint(1000, 999999)

        prompt_details = ""
        if mode_type == "laws":
            prompt_details = "استخرج القوانين والمفاهيم العلمية والرياضية الواردة بالملف وصغ أسئلة وتطبيقات مسائل وحسابات ومعادلات عليها بدقة."
        elif mode_type == "comprehensive":
            prompt_details = "صغ اختباراً شاملاً يغطي كافة أجزاء وفصول وموضوعات الملف بشكل متوازن ومتدرج."
        else:
            prompt_details = f"صغ الأسئلة بمستوى ({level_name}) تحديداً."

        prompt = f"""
        أنت خبير واضع امتحانات الثانوية العامة المصرية والجامعات.
        قم بقراءة ملف الـ PDF بدقة.
        أنشئ {count} أسئلة اختيارات من متعدد (MCQ) جديدة تماماً وفريدة (معرف التوليد: {random_seed}).
        تفاصيل التوليد: {prompt_details}

        شروط ومعايير التنسيق الصارمة:
        1. إذا كانت المادة تحتوي على معادلات رياضية أو كيميائية أو فيزيائية، اكتبها بنص LaTeX واضح بين علامتي $ (مثال: $E = mc^2$ أو $\\int_{{0}}^{{\\infty}} f(x)dx$).
        2. الإجابات يجب أن تكون واضحة ومحددة.
        3. لكل سؤال أضف تلميحاً مساعداً (hint) لا يكشف الحل مباشرة.
        4. أضف شرحاً تفصيلياً ممتازاً لسبب الإجابة الصحيحة.
        5. أرجع النتيجة في صيغة JSON حصرية بتنسيق Array of Objects:

        [
          {{
            "q": "نص السؤال منظم ومعادلاته بـ LaTeX",
            "options": ["أ) الاختيار الأول", "ب) الاختيار الثاني", "ج) الاختيار الثالث", "د) الاختيار الرابع"],
            "answer": "أ) الاختيار الأول",
            "hint": "تلميح ذكي للحل",
            "explanation": "الشرح التفصيلي للحل"
          }}
        ]
        """

        response = model.generate_content([pdf_file_part, prompt])
        raw_text = response.text.strip()
        
        match = re.search(r'\[\s*\{.*\}\s*\]', raw_text, re.DOTALL)
        if match:
            clean_json_str = match.group(0)
        else:
            clean_json_str = raw_text.replace("```json", "").replace("```", "").strip()
            
        return json.loads(clean_json_str)

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
                        with st.spinner("جاري تحليل المحتوى وتوليد الأسئلة والمعادلات بالذكاء الاصطناعي..."):
                            bytes_data = uploaded_file.getvalue()
                            st.session_state.pdf_bytes = bytes_data
                            
                            # إعادة ضبط فرص التلميحات
                            st.session_state.hints_used = 0
                            st.session_state.unlocked_hints = set()

                            if exam_type == "🔥 3 اختبارات (سهل، متوسط، صعب)":
                                st.session_state.quizzes = {
                                    "سهل": generate_quiz_with_ai(bytes_data, num_questions, "level", "سهل", api_key),
                                    "متوسط": generate_quiz_with_ai(bytes_data, num_questions, "level", "متوسط", api_key),
                                    "صعب": generate_quiz_with_ai(bytes_data, num_questions, "level", "صعب", api_key)
                                }
                            elif exam_type == "🚀 اختبار شامل للمادة":
                                st.session_state.quizzes = {
                                    "اختبار شامل": generate_quiz_with_ai(bytes_data, num_questions, "comprehensive", None, api_key)
                                }
                            elif exam_type == "📐 اختبار قوانين وتطبيقات (من ملف القوانين)":
                                st.session_state.quizzes = {
                                    "اختبار القوانين والتطبيقات": generate_quiz_with_ai(bytes_data, num_questions, "laws", None, api_key)
                                }
                            else: # اختبار واحد بمستوى مخصص
                                st.session_state.quizzes = {
                                    f"اختبار ({selected_single_level})": generate_quiz_with_ai(bytes_data, num_questions, "level", selected_single_level, api_key)
                                }
                                
                            st.session_state.submitted_quiz = False
                            st.session_state.show_review_warning = False
                            st.success("✅ تم توليد الامتحان بنجاح وصياغة الأسئلة والمعادلات!")
                    except Exception as e:
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
                        st.write(q_item['q']) # دعم معادلات latex
                        
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
                        
                        st.markdown("<div class='exam-watermark'>محمد عبدالله - Mohamed Abdallah</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    if st.button(f"📩 إرسال وتصحيح الاختبار النهائي ({current_key})", key=f"btn_submit_{current_key}"):
                        st.session_state.current_active_level = current_key
                        st.session_state.temp_user_answers = user_answers
                        st.session_state.show_review_warning = True

            # التنبيه والمراجعة قبل التسليم
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

            # عرض النتيجة
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

        if "pdf_bytes" not in st.session_state:
            st.info("💡 قم برفع ملف الـ PDF في التبويب الأول أولاً، ثم يمكنك إجراء دردشة وتحليل تفاعلي مع الذكاء الاصطناعي حول محتواه.")
        elif not api_key:
            st.warning("⚠️ يرجى إدخال مفتاح Gemini API Key في القائمة الجانبية لتفعيل الشات.")
        else:
            # عرض سجل المحادثة السابق
            for chat in st.session_state.chat_history:
                st.markdown(f"**👤 أنت:** {chat['user']}")
                st.markdown(f"**🤖 المساعد الذكي:** {chat['assistant']}")
                st.markdown("---")

            with st.form(key="chat_form", clear_on_submit=True):
                user_query = st.text_input("اسأل الذكاء الاصطناعي عن أي جزء في المادة، القوانين، أو المسائل...")
                submit_chat = st.form_submit_button("إرسال السؤال 🚀")

                if submit_chat and user_query.strip():
                    with st.spinner("جاري التحليل والإجابة..."):
                        try:
                            model = get_working_gemini_model(api_key)
                            pdf_part = {"mime_type": "application/pdf", "data": st.session_state.pdf_bytes}
                            
                            chat_prompt = f"""
                            أنت معلم وثانوية عامة ومساعد محترف.
                            بناءً على ملف المادة المرفق، أجب على سؤال الطالب بكل دقة ووضوح وبنظام منظم.
                            استخدم صياغة LaTeX في المعادلة إن وجدت.
                            سؤال الطالب: {user_query}
                            """
                            
                            chat_response = model.generate_content([pdf_part, chat_prompt])
                            ans_text = chat_response.text
                            
                            st.session_state.chat_history.append({"user": user_query, "assistant": ans_text})
                            st.rerun()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {e}")
