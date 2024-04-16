# importing libraries
import streamlit as st
import pandas as pd
import base64,random
import time,datetime
#libraries to parse the resume pdf files
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io,random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
import yt_dlp
import matplotlib.pyplot as plt
import plotly.express as px #to create visualisations at the admin session
import nltk
# nltk.download('stopwords')


# def fetch_yt_video(link):
#     video = pafy.new(link)
#     return video.title

def fetch_yt_video(link):
    with yt_dlp.YoutubeDL({"no_warnings": True}) as ydl:
        info = ydl.extract_info(link, download=False)
    return info["title"]


def get_table_download_link(df,filename,text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams(detect_vertical=True))
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file,'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
            # print(page)
        text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path,'rb') as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader('**Courses & Certificates Recommendations 🎓**')
    c = 0
    rec_course = []
    no_of_rec = st.slider('Choose number of Courses to Recommend',1,10,5)
    random.shuffle(course_list)
    for c_name,c_link in course_list:
        c += 1
        st.markdown(f'({c}) [{c_name}]({c_link})')
        rec_course.append(c_name)
        if c==no_of_rec:
            break
    return rec_course


# connection to database
connection = pymysql.connect(host= 'localhost', user='root', password='bhaveshk', db='cv')
cursor = connection.cursor()

def insert_data(name,email,res_score,timestamp,no_of_pages,reco_field,cand_level,skills,recommended_skills,courses):
    db_table_name = 'user_data'
    insert_record = 'insert into ' + db_table_name + ' values(0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
    rec_values = (name,email,str(res_score),timestamp,str(no_of_pages),reco_field,cand_level,skills,recommended_skills,courses)
    cursor.execute(insert_record, rec_values)
    connection.commit()

st.set_page_config(page_title='Resume Analyzer', 
                   page_icon='Logo/resume_icon.jpg')

def run():
    img = Image.open('Logo/resume_img.png')
    img.resize((250,250))
    st.image(img)
    st.title('AI Resume Analyzer')
    st.sidebar.markdown('# Choose User')
    activites = ['User', 'Admin']
    choice = st.sidebar.selectbox('Choose among the options:', activites)
    link = '[@Developed by Bhavesh](https://www.linkedin.com/in/bhavesh-kabdwal/)'
    st.sidebar.markdown(link, unsafe_allow_html=True)

    # creating database
    db_sql = 'CREATE DATABASE IF NOT EXISTS CV;'
    cursor.execute(db_sql)

    # creating table
    db_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + db_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(500) NOT NULL,
                     Email_ID VARCHAR(500) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field TEXT NOT NULL,
                     User_level Text NOT NULL,
                     Actual_skills Text NOT NULL,
                     Recommended_skills Text NOT NULL,
                     Recommended_courses Text NOT NULL,
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)

    if choice=='User':
        st.markdown('''<h5 style='text-align: left; color: #FCF90E;'> Upload your resume, and get smart recommendations</h5>''', unsafe_allow_html=True)
        pdf_file = st.file_uploader('Upload your Resume', type=['pdf'])
        if pdf_file is not None:
            with st.spinner('Uploading your Resume . . .'):
                time.sleep(4)
            save_pdf_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_pdf_path, 'wb') as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_pdf_path)
            resume_data = ResumeParser(save_pdf_path).get_extracted_data()
            if resume_data['total_experience']:
                print('\n\n\n'+ str(resume_data['total_experience'])+'\n\n\n')
            else: 
                print('\n\n\nhi\n\n\n')
            if resume_data:
                #get all the resume data
                resume_text = pdf_reader(save_pdf_path)

                st.header('**Resume Analysis**')
                st.success('Hello ' + resume_data['name'])
                st.subheader('**Your Basic Info**')
                try:
                    st.text('NAME         : '+ resume_data['name'])
                    st.text('EMAIL        : '+ resume_data['email'])
                    st.text('CONTACT      : '+ resume_data['mobile_number'])
                    st.text('RESUME PAGES : '+ str(resume_data['no_of_pages']))
                except:
                    pass
                
                cand_level = ''
                if resume_data['total_experience'] < 3:
                    cand_level = "Fresher"
                    st.markdown( '''<h4 style='text-align: center; color: #d73b5c;'>You are at Fresher level!</h4>''',unsafe_allow_html=True)
                elif resume_data['total_experience'] >= 3 and resume_data['total_experience'] <=10:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: center; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif resume_data['no_of_pages'] > 10:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: center; color: #fba171;'>You are at experience level!</h4>''',unsafe_allow_html=True)

                st.subheader('**Skills Recommendation**💡')
                keywords = st_tags(label='#### Your Current Skills', text='See our recommended skills below', value=resume_data['skills'], key='1  ')

                ##  keywords
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''

                # courses Recommendation
                for i in resume_data['skills']:
                    
                    #data science recommendation
                    if i.lower() in ds_keyword:
                        reco_field = 'Data Science'
                        st.success('** Our Analysis says you are looking for a Data Science Job**')
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.', text='Recommended skills generated from System', value=recommended_skills, key = '2')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job</h4>''',unsafe_allow_html=True)
                        rec_course =  course_recommender(ds_course)
                        break
                    
                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break

                # insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+' '+cur_time)

                # Resume writing recommendations
                st.subheader('**Resume Tips & Ideas💡**')
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score+20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #FE0523;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)

                if 'Declaration'  in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration/h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #FE0523;'>[-] Please add Declaration. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',unsafe_allow_html=True)

                if 'Hobbies' or 'Interests'in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #FE0523;'>[-] Please add Hobbies. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',unsafe_allow_html=True)

                if 'Achievements' or 'Skills' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Skills </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #FE0523;'>[-] Please add Skills. It will show that you are capable for the required position.</h4>''',unsafe_allow_html=True)

                if 'Projects' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #FE0523;'>[-] Please add Projects. It will show that you have done work related the required position or not.</h4>''',unsafe_allow_html=True)

                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' +str(score)+ '**')
                st.warning('** Note: This score is based on your content that you have in Resume. **')
                st.balloons()

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                              str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']),
                              str(recommended_skills), str(rec_course))
                
                #resume writing video
                st.header('**Bonus Video for Resume Writing Tips💡**')
                resume_vid = random.choice(resume_videos)
                res_vid_title = fetch_yt_video(resume_vid)
                st.subheader("✅ **"+res_vid_title+"**")
                st.video(resume_vid)

                 #interview preparation tips
                st.header('**Bonus Video for Interview Tips💡**')
                interview_vid = random.choice(interview_videos)
                interview_vid_title = fetch_yt_video(interview_vid)
                st.subheader("✅ **"+interview_vid_title+"**")
                st.video(interview_vid)

                connection.commit()
            else:
                st.error('** Something went wrong **')

    
    else:
        ## Admin side
        st.success('** Welcome to Admin Side **')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'bhavesh' and ad_password == 'bhaveshk22':
                st.success("Welcome Bhavesh !")

                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df,'User_Data.csv','Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)
                
                ## Pie chart for predicted field recommendations
                labels = plot_data.Predicted_Field.unique()
                
                values = plot_data.Predicted_Field.value_counts()
                
                st.subheader("**Pie-Chart for Predicted Field Recommendation**")
                
                fig, ax = plt.subplots()
                fig.patch.set_facecolor('#262730')
                ax.pie(values, labels=labels, autopct='%1.1f%%', radius=0.6, textprops={'fontsize': 7, 'color':'white'})
                st.pyplot(fig, use_container_width=False)

                ### Pie chart for User's👨‍💻 Experienced Level
                labels = plot_data.User_level.unique()
                values = plot_data.User_level.value_counts()
                
                st.subheader("**Pie-Chart for User's Experienced Level**")
                fig, ax = plt.subplots()
                fig.patch.set_facecolor('#262730')
                ax.pie(values, labels=labels, autopct='%1.1f%%', radius=0.6, textprops={'fontsize': 7,'color':'white'})
                st.pyplot(fig, use_container_width=False)
                

            else:
                st.error("Wrong ID & Password Provided")



run()