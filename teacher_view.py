import sys
import tkinter as tk
from tkinter import messagebox
from copy import copy

import pickle
from threading import Thread, enumerate
from socket import AF_INET, socket, SOCK_STREAM, gethostname, gethostbyname

from os import listdir
import datetime


PORT = 44000


'''
DEFINE MESSAGE CODE ENUMS
'''
ANSWER = 0
QUESTION = 1
MSG = 2
CONN = 3
QUIZ = 4
ANSWERS = 5


class Main_View:
	def __init__(self, main):
		'''
		Initiate Teacher_view class
		'''

		self.main = main
		self.main.title('Main')
		self.main.resizable(False, False)

		self.teacher_view()

	def teacher_view(self):
		self.t_app = Teacher_View(self.main)

class Teacher_View:
	'''
	In Teacher_View class, a teacher is able to receive messages from students and create/send quizzes to students.
	'''

	def __init__(self, teacher):
		'''
		BEGIN NETWORKING SET UP
		'''
		self.host = ''
		self.port = PORT
		self.bufsiz = 4096
		self.addr = (self.host, self.port)
		self.server = socket(AF_INET, SOCK_STREAM)
		self.server.bind(self.addr)
		self.server.listen(5)
		self.hostname = gethostname()
		self.ip_addr = gethostbyname(self.hostname)

		self.clients = {}
		self.addresses = {}
		'''
		END NETWORKING SET UP
		'''

		self.quitting = False
		self.m_list = []
		self.student_count = 0
		self.current_quiz = None
		self.current_question = None
		self.qe_list = []
		self.temp_qe_list = []
		self.qu_list = []
		self.answer_list = []
		self.edit = False

		#Load Quizzes
		l = listdir("quizes")
		for item in l:
			d = self.load_quiz_file(item)
			if d:
				self.qu_list.append(d)


		self.teacher = teacher
		self.teacher.title("Teacher")

		#initial message dialog
		self.init_dialog()
		#initial frame for making quizzes
		self.init_quizFrame()

		#Insert list of quizzes into Listbox 
		for item in self.qu_list:
			self.quiz_list.insert(tk.END, item['name'])

		self.accept_thread = Thread(target=self.accept_connections)
		self.accept_thread.start()

		self.teacher.protocol('WM_DELETE_WINDOW', self.closeWin)

		#For Testing
		# q = {'name': 'SampleQuiz', 'questions':[], 'hash':9999, 'description':'This is a Sample Quize with no questions'}
		# self.create_quiz_file(q)
		# print(self.load_quiz_file('quizes/jieunquiz.qz'))



	'''
	Begin Networking Methods
	'''
	def broadcast(self, quiz):
		m = pickle.dumps(quiz)
		for sock in self.clients:
			sock.send(m)

	def accept_connections(self):
		try:
			while True:
				client, client_address = self.server.accept()
				self.addresses[client] = client_address
				Thread(target=self.handle_connection, args=(client,)).start()
		except ConnectionAbortedError as e:
			# print(e)
			pass

	def handle_connection(self,client):
		self.student_count += 1
		self.student_conn['text'] = 'Student count: ' + str(self.student_count)

		og_conn = client.recv(self.bufsiz)
		d = pickle.loads(og_conn)
		name = d["name"]

		# self.logmsg(name + " has joined")
		self.clients[client] = name
		try:
			while True:

				if self.quitting:
					break
				
				m_conn = client.recv(self.bufsiz)

				d = pickle.loads(m_conn)
				m_type = d["type"]

				if m_type == MSG:
					self.logmsg(name +': '+ d["msg"])
					self.m_list.append(name +': '+ d["msg"])

				elif m_type == CONN:
					self.student_count -= 1
					self.student_conn['text'] = 'Student count: ' + str(self.student_count)

					client.close()
					del self.clients[client]
					break

				elif m_type == ANSWER:
					print(d)

				elif m_type == ANSWERS:
					self.answer_list.append(d)

		except Exception as e:
			pass
	'''
	End Networking methods
	'''

	def logmsg(self, message):
		'''
		Display received messages from student
		'''
		if(message):
			self.msg_list.insert(tk.END, message)

	def init_dialog(self):
		'''
		Initial dialog representing host and IP address on the top of the application and LOGOUT Button.
		'''
		self.Main_Frame_T = tk.Frame(self.teacher, height = 30, width = 100)
		self.Main_Frame_T.grid(row=0, column=0)
		self.Main_Frame_T.pack()

		self.log_outButton = tk.Button(self.Main_Frame_T, text="LOGOUT", command = self.quit)
		self.log_outButton.pack(side=tk.LEFT)

		self.IP = tk.Label(self.Main_Frame_T, text='IP Address: ' + self.ip_addr)
		self.IP.pack(side=tk.LEFT)
		self.msg_frame()

	def msg_frame(self):
		#Message dialog frame
		self.messages_frame = tk.Frame(self.teacher, relief = tk.RAISED, borderwidth = 1)
		self.messages_frame.grid(row = 0, column = 0, padx = 0, pady =0)
		self.messages_frame.pack(side = tk.LEFT,fill=tk.Y)

		self.dialog_frame = tk.Frame(self.messages_frame, height = 20, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.dialog_frame.grid(row=0, column=0)
		self.dialog_frame.pack()
		#scrollbar for dialog
		self.scrollbar_1 = tk.Scrollbar(self.dialog_frame, orient = tk.VERTICAL)
		self.scrollbar_1.pack(side=tk.RIGHT, fill=tk.Y)

		#messages will be displayed on msg_list
		self.msg_list = tk.Listbox(self.dialog_frame, height=20, width=50, yscrollcommand=self.scrollbar_1.set)
		self.msg_list.grid(row=0, column = 1)
		self.msg_list.pack()

		self.scrollbar_1.config(command = self.msg_list.yview)

		#Counting the number of students joining application and display
		self.student_conn = tk.Label(self.messages_frame, text = "Student count: 0")
		self.student_conn.pack(side = tk.LEFT)

	def init_quizFrame(self):
		#Top Frame
		self.quiz_frame = tk.Frame(self.teacher, relief= tk.RAISED, borderwidth = 1)
		self.quiz_frame.grid(row = 0, column = 1, padx = 0, pady = 0)
		self.quiz_frame.pack(side = tk.RIGHT, fill = tk.Y)

		self.quiz_list_frame = tk.Frame(self.quiz_frame, height = 20, width = 50, relief= tk.RAISED, borderwidth = 1)
		self.quiz_list_frame.grid(row=0, column=0)
		self.quiz_list_frame.pack()

		self.scrollbar_2 = tk.Scrollbar(self.quiz_list_frame, orient = tk.VERTICAL)
		self.scrollbar_2.pack(side = tk.RIGHT, fill = tk.Y)
		#Listbox to display list of quizzes
		self.quiz_list = tk.Listbox(self.quiz_list_frame, height = 20, width = 50, yscrollcommand = self.scrollbar_2.set)
		self.quiz_list.grid(row=0, column = 0)
		self.quiz_list.pack(side = tk.TOP)

		self.scrollbar_2.config(command = self.quiz_list.yview)

		# Select the quiz to renew current_quiz
		self.quiz_list.bind('<<ListboxSelect>>', self.selected_quiz)

		#NEW Button to create new quiz
		self.show_button = tk.Button(self.quiz_frame, text="NEW", command=self.show_quiz)
		self.show_button.pack(side=tk.LEFT, expand = True)
		#OPEN Button to edit/see quiz
		self.show_button = tk.Button(self.quiz_frame, text="OPEN", command = self.open_quiz)
		self.show_button.pack(side=tk.LEFT, expand = True)
		#DELETE Button to delete the quiz
		self.show_button = tk.Button(self.quiz_frame, text="DELETE", command = self.delete_quiz)
		self.show_button.pack(side=tk.LEFT, expand = True)
		#SEND QUIZ Button to send quiz to students
		self.send_button = tk.Button(self.quiz_frame, text="SEND QUIZ", command = self.send_quiz)
		self.send_button.pack(side=tk.RIGHT, expand = True)

		####IS THIS BEING USED?
		self.get_quiz()

	def show_quiz(self):
		#Reset frame
		self.quiz_frame.destroy()
		#Display new frame
		self.make_quizFrame()
		self.temp_qe_list.clear()

	def make_quizFrame(self):
		'''
		Make new frame for creating new quiz
		'''
		self.create = tk.Frame(self.teacher, relief = tk.RAISED, borderwidth = 1)
		self.create.grid(row = 0, column = 0, padx = 0, pady =0)
		self.create.pack(side = tk.LEFT,fill=tk.Y)

		self.dialog_frame1 = tk.Frame(self.create, height = 10, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.dialog_frame1.grid(row=0, column=0)
		self.dialog_frame1.pack()

		self.quiz_label = tk.Label(self.dialog_frame1, text = "Title").pack(side = tk.TOP)
		self.my_quizTitle = tk.StringVar()
	
		self.quiz_title = tk.Entry(self.dialog_frame1, textvariable = self.my_quizTitle)
		self.quiz_title.grid(row=0, column = 0)
		self.quiz_title.pack()
		self.quiz_dLabel = tk.Label(self.dialog_frame1, text = "Description").pack(side = tk.TOP)

		self.my_quizD = tk.StringVar()
		self.quiz_description = tk.Text(self.dialog_frame1, height = 3, width = 59, highlightthickness=1, highlightbackground="Black")
		self.quiz_description.grid(row=0, column = 0)
		self.quiz_description.pack()

		self.add_question_label = tk.Label(self.dialog_frame1, text = 'Please add questions below')
		self.add_question_label.pack(side = tk.LEFT)
		self.back_button = tk.Button(self.dialog_frame1, text = 'Back', command = self.create_back)
		self.back_button.pack(side= tk.RIGHT)
		self.open_question_frame()

	def question_frame(self):
		'''
		Create new frame for creating question
		'''
		self.dialog_frame2 = tk.Frame(self.create, height = 20, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.dialog_frame2.grid(row=1, column=0)
		self.dialog_frame2.pack()

		self.button_frame = tk.Frame(self.create, height=10, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.button_frame.grid(row=2, column=0)
		self.button_frame.pack()

		self.scrollbar_2 = tk.Scrollbar(self.dialog_frame2, orient = tk.VERTICAL)
		self.scrollbar_2.pack(side=tk.RIGHT, fill=tk.Y)

		self.radio_area = tk.Listbox(self.dialog_frame2, height = 11, width = 50, yscrollcommand=self.scrollbar_2.set)
		self.radio_area.grid(row=0, column=0)
		self.radio_area.pack()

		self.scrollbar_2.config(command = self.radio_area.yview)

		self.radio_area.bind('<<ListboxSelect>>', self.selected_question)

		self.add_button = tk.Button(self.button_frame, text = 'ADD', command = self.add_radio)
		self.add_button.pack(side = tk.LEFT)

		self.edit_button = tk.Button(self.button_frame, text='EDIT', command = self.new_edit_question)
		self.edit_button.pack(side = tk.LEFT)

		self.delete_button = tk.Button(self.button_frame, text='DELETE', command = self.delete_question)
		self.delete_button.pack(side=tk.LEFT)

		self.create_quiz_button = tk.Button(self.button_frame, text='CREATE QUIZ', command = self.quiz_get)
		self.create_quiz_button.pack(side=tk.LEFT)

	def new_edit_question(self):
		'''
		When EDIT button clicked to edit question, identify which question has been clicked
		by calling self.selected_question and if the self.current_question exists, call self.edit_radio()

		'''
		self.radio_area.bind('<<ListboxSelect>>', self.selected_question)
		if self.current_question != None:
			self.edit_radio()
		else:
			messagebox.showerror("Select Error", "No question selected.")

	def edit_question_back(self):
		'''
		Destroy old frame and back to the previous frame and add question list
		'''
		self.dialog_frame2.destroy()
		self.button_frame.destroy()
		self.done_button.destroy()
		self.Back_button.destroy()
		self.open_question_frame()
		for i in range(len(self.qe_list)):
			self.radio_area.insert(tk.END, "Question "+str(i+1)+" :"+self.qe_list[i]['question'])

	def edit_radio(self):
		'''
		Generate radio buttons that have corresponding contents of quiz when a user select specific question
		'''
		self.add_button.destroy()
		self.edit_button.destroy()
		self.delete_button.destroy()
		self.create_quiz_button.destroy()
		self.scrollbar_2.destroy()
		self.radio_area.destroy()

		self.problem_label = tk.Label(self.dialog_frame2, text = 'Question').place(x = 10, y = 5)
		self.q_content = tk.StringVar(self.dialog_frame2, value = self.current_question['question'])
		self.problem = tk.Entry(self.dialog_frame2, textvariable = self.q_content, width = 30)
		self.problem.place(x=70, y=5)

		# get correct answer
		num_b = {'A' : 1, 'B' : 2, 'C' : 3, 'D' : 4, 'E' : 5}
		ans = self.current_question['answer']

		#Radio Buttons
		self.term = tk.IntVar()
		if ans:
			self.term.set(num_b[ans])
		self.b1 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 1).place(x=5, y = 40)
		self.option1 = tk.StringVar(self.dialog_frame2, value = self.current_question['A'])
		self.input1 = tk.Entry(self.dialog_frame2, textvariable = self.option1, width=45).place(x=30, y=40)

		self.b2 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 2).place(x=5, y = 70)
		self.option2 = tk.StringVar(self.dialog_frame2, value = self.current_question['B'])
		self.input2 = tk.Entry(self.dialog_frame2, textvariable = self.option2, width=45).place(x=30, y=70)

		self.b3 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 3).place(x=5, y = 100)
		self.option3 = tk.StringVar(self.dialog_frame2, value = self.current_question['C'])
		self.input3 = tk.Entry(self.dialog_frame2, textvariable = self.option3, width=45).place(x=30, y=100)

		self.b4 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 4).place(x=5, y = 130)
		self.option4 = tk.StringVar(self.dialog_frame2, value = self.current_question['D'])
		self.input4 = tk.Entry(self.dialog_frame2, textvariable = self.option4, width=45).place(x=30, y=130)

		self.b5 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 5).place(x=5, y = 160)
		self.option5 = tk.StringVar(self.dialog_frame2, value = self.current_question['E'])
		self.input5 = tk.Entry(self.dialog_frame2, textvariable = self.option5, width=45).place(x=30, y=160)

		self.done_button = tk.Button(self.button_frame, text = 'CHANGE', command = self.question_change_get)
		self.done_button.pack(side = tk.LEFT)

		self.Back_button = tk.Button(self.button_frame, text='BACK', command = self.edit_question_back)
		self.Back_button.pack(side = tk.LEFT)

	def question_change_get(self):
		'''
		Get value from radio buttons and store changed value into the qu_list and qe_list
		'''

		ans_dict = {1 : "A", 2 : "B", 3 : "C", 4 : "D", 5 : "E"}
		a = self.term.get()
		q = self.q_content.get()
		A = self.option1.get()
		B = self.option2.get()
		C = self.option3.get()
		D = self.option4.get()
		E = self.option5.get()
		if q and a and A and B and C and D and E:
			answer = ans_dict[a]
			dict_qe = self.dict_question(answer, q, A, B, C, D, E)
			#remove old question
			self.qe_list.remove(self.current_question)
			#append new question
			self.qe_list.append(dict_qe)
			self.temp_qe_list = self.qe_list
			messagebox.showinfo("Change Question", "Finish changed a question.")
			self.dialog_frame2.destroy()
			self.button_frame.destroy()
			self.done_button.destroy()
			self.Back_button.destroy()
			self.open_question_frame()
			#re-display list of questions
			for i in range(len(self.temp_qe_list)):
				self.radio_area.insert(tk.END, "Question "+str(i+1)+" :"+self.temp_qe_list[i]['question'])
		else:
			if not q:
				messagebox.showerror("Input Error", "Please input question.")
			elif not A or not B or not C or not D or not E:
				messagebox.showerror("Input Error", "Please input all answer options.")
			elif not a:
				messagebox.showerror("Input Error", "Please select a correct answer.")

	''''''''''''''''''''''''''''''''

	def open_quizFrame(self):
		# same function as make_quizFrame, retrive data for OPEN button
		self.radio_Count = 0

		self.create = tk.Frame(self.teacher, relief = tk.RAISED, borderwidth = 1)
		self.create.grid(row = 0, column = 0, padx = 0, pady =0)
		self.create.pack(side = tk.LEFT,fill=tk.Y)

		self.dialog_frame1 = tk.Frame(self.create, height = 10, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.dialog_frame1.grid(row=0, column=0)
		self.dialog_frame1.pack()

		#messages will be displayed on msg_list
		self.quiz_label = tk.Label(self.dialog_frame1, text = "Title").pack(side = tk.TOP)
		# default value for quiz name
		self.name = self.current_quiz['name']
		self.my_quizTitle = tk.StringVar(self.dialog_frame1, value = self.name)
		self.quiz_title = tk.Entry(self.dialog_frame1, textvariable = self.my_quizTitle)
		self.quiz_title.grid(row=0, column = 0)
		self.quiz_title.pack()

		self.quiz_dLabel = tk.Label(self.dialog_frame1, text = "Description").pack(side = tk.TOP)

		self.my_quizD = tk.StringVar()

		self.quiz_description = tk.Text(self.dialog_frame1, height = 3, width = 59, highlightthickness=1, highlightbackground="Black")
		# default value for text
		self.quiz_description.insert(tk.END, self.current_quiz['description'])
		self.quiz_description.grid(row=0, column = 0)
		self.quiz_description.pack()

		self.add_question_label = tk.Label(self.dialog_frame1, text = 'Please add questions below')
		self.add_question_label.pack(side = tk.LEFT)
		#Open previous frame
		self.back_button = tk.Button(self.dialog_frame1, text = 'Back', command = self.create_back)
		self.back_button.pack(side= tk.RIGHT)
		self.open_question_frame()


	def open_quiz(self):
		'''
		When a user clicks one of quizzes from quiz_list, and clicks open button to edit,
		it displays new frame for editing quiz&questions and corresponding data for the quiz
		''' 
		if self.quiz_list.curselection():
			self.quiz_frame.destroy()
			self.open_quizFrame()
			# print(self.current_quiz['questions'])
			for question in self.current_quiz['questions']:
				self.qe_list.append(question)
			for q in range(len(self.current_quiz['questions'])):
				self.radio_area.insert(tk.END, "Question "+str(q)+": "+self.current_quiz['questions'][q]['question'])
		else:
			messagebox.showerror("Select Error", "No quiz selected.")

	def delete_quiz(self):
		'''
		Delete quiz when a specific quiz is chosen
		'''
		if self.current_quiz:
			self.qu_list.remove(self.current_quiz)
			try:
				remove("quizes/" + self.current_quiz['name'] + ".qz")
			except Exception as e:
				pass
			self.current_quiz = None
			selection = self.quiz_list.curselection()
			self.quiz_list.delete(selection[0])


	def create_back(self):
		'''
		Go back to previous frame without saving quiz/question
		'''
		self.create.destroy()
		self.init_quizFrame()
		for item in self.qu_list:
			self.quiz_list.insert(tk.END, item['name'])

	def open_question_frame(self):
		'''
		Open making question frame when a user tries to edit 
		'''
		self.dialog_frame2 = tk.Frame(self.create, height = 20, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.dialog_frame2.grid(row=1, column=0)
		self.dialog_frame2.pack()

		self.button_frame = tk.Frame(self.create, height=10, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.button_frame.grid(row=2, column=0)
		self.button_frame.pack()


		#self.question_text = tk.Label(self.dialog_frame2, text = "Type quiz prob here.").pack(side = tk.TOP)
		self.scrollbar_2 = tk.Scrollbar(self.dialog_frame2, orient = tk.VERTICAL)
		self.scrollbar_2.pack(side=tk.RIGHT, fill=tk.Y)

		self.radio_area = tk.Listbox(self.dialog_frame2, height = 11, width = 50, yscrollcommand=self.scrollbar_2.set)
		self.radio_area.grid(row=0, column=0)
		self.radio_area.pack()

		self.scrollbar_2.config(command = self.radio_area.yview)

		#Bind radio_area with self.selected_question to identify which questions is being selected
		self.radio_area.bind('<<ListboxSelect>>', self.selected_question)
		#Add_question
		self.add_button = tk.Button(self.button_frame, text = 'ADD', command = self.add_radio)
		self.add_button.pack(side = tk.LEFT)
		#Edit question
		self.edit_button = tk.Button(self.button_frame, text='EDIT', command = self.open_edit_question)
		self.edit_button.pack(side = tk.LEFT)
		#Delete question
		self.delete_button = tk.Button(self.button_frame, text='DELETE', command = self.delete_question)
		self.delete_button.pack(side=tk.LEFT)
		#Save Changes
		self.create_quiz_button = tk.Button(self.button_frame, text='SAVE CHANGE', command = self.quiz_change)
		self.create_quiz_button.pack(side=tk.LEFT)


	def open_edit_question(self):
		self.radio_area.bind('<<ListboxSelect>>', self.selected_question)

		#if self.current_question exists, open frame with radio button containg all data
		if self.current_question != None:
			self.open_edit_radio()
		else:
			messagebox.showerror("Select Error", "No question selected.")

	def delete_question(self):
		'''
		delete selected question
		'''
		if self.current_question != None:
			self.qe_list.remove(self.current_question)
			self.current_question = None
			selection = self.radio_area.curselection()
			self.radio_area.delete(selection[0])
		else:
			messagebox.showerror("Delete Error", "No question selected.")

	def quiz_change(self):
		'''
		Store changed quizzes and reset frame
		'''
		name = self.my_quizTitle.get()
			# print(name)
		if name:
			questions = copy(self.qe_list)
			description = self.quiz_description.get("1.0", tk.END)
			quiz_dict = self.dict_quiz(name, questions, description)
			#Update changed quiz into file
			self.create_quiz_file(quiz_dict)
			#remove old quiz
			self.qu_list.remove(self.current_quiz)
			#add new quiz
			self.qu_list.append(quiz_dict)
			#reset frame
			self.create.destroy()
			self.init_quizFrame()
			#display list of quizzes
			for item in self.qu_list:
				self.quiz_list.insert(tk.END, item['name'])

	def quiz_get(self):
		'''
		When a user creates new quiz, it stores data into lists of quizzes and question
		and display as list of quizzes
		'''
		name = self.my_quizTitle.get()
		# print(name)
		if name:
			questions = copy(self.qe_list)
			description = self.quiz_description.get("1.0", tk.END)
			quiz_dict = self.dict_quiz(name, questions, description)
			self.create_quiz_file(quiz_dict)
			self.qu_list.append(quiz_dict)
			self.create.destroy()
			self.init_quizFrame()
			for item in self.qu_list:
				self.quiz_list.insert(tk.END, item['name'])

	def dict_question(self, answer, question, A, B, C, D, E):
		'''
		Create dictionary of questions
		'''
		l = locals()
		del l['self']

		question_dict = {}
		question_dict['type'] = QUESTION
		question_dict['answer'] = answer
		question_dict['question'] = question
		question_dict['A'] = A
		question_dict['B'] = B
		question_dict['C'] = C
		question_dict['D'] = D
		question_dict['E'] = E

		h = sum([hash(item) for item in l.values()])
		question_dict['hash'] = h

		return question_dict

	def dict_quiz(self, name, questions, description = '', time = 10000):
		'''
		Create dictionary of quizzes
		'''
		quiz_dict = {}
		quiz_dict['type'] = QUIZ
		quiz_dict['name'] = name
		quiz_dict['time'] = time
		quiz_dict['questions'] = questions
		quiz_dict['description'] = description

		#Creating hash
		q_hash = [hash(item['hash']) for item in questions]
		h = hash(name) + hash(time)
		if q_hash:
			h += sum(q_hash)
		quiz_dict['hash'] = h

		return quiz_dict

	# def send_question(self):
	# 	if messagebox.askyesno("Send Prompt", "Are you sure you want to send the question?"):
	# 		self.broadcast(self.quiz)

	def send_quiz(self):
		'''
		When a user(teacher) wants to send created quiz to students,
		calls self.broadcast(send_quiz)
		'''
		self.quiz_list.bind('<<ListboxSelect>>', self.selected_quiz)
		send_quiz = self.current_quiz
		if send_quiz:
			if messagebox.askyesno("Send Prompt", "Are you sure you want to send the quiz?"):
				self.broadcast(send_quiz)
				self.current_quiz = None
		else:
			messagebox.askyesno("Send Prompt", "You have not selected a quiz.")

	def add_radio(self):
		'''
		Add_radio button when a user wants to create questions and destroy old frames
		'''
		self.add_button.destroy()
		self.edit_button.destroy()
		self.delete_button.destroy()
		self.create_quiz_button.destroy()
		self.scrollbar_2.destroy()
		self.radio_area.destroy()

		self.problem_label = tk.Label(self.dialog_frame2, text = 'Question').place(x = 10, y = 5)
		self.q_content = tk.StringVar()
		self.problem = tk.Entry(self.dialog_frame2, textvariable = self.q_content, width = 30)
		self.problem.place(x=70, y=5)

		self.term = tk.IntVar()
		self.b1 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 1).place(x=5, y = 40)
		self.option1 = tk.StringVar()
		self.input1 = tk.Entry(self.dialog_frame2, textvariable = self.option1, width=45).place(x=30, y=40)

		self.b2 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 2).place(x=5, y = 70)
		self.option2 = tk.StringVar()
		self.input2 = tk.Entry(self.dialog_frame2, textvariable = self.option2, width=45).place(x=30, y=70)

		self.b3 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 3).place(x=5, y = 100)
		self.option3 = tk.StringVar()
		self.input3 = tk.Entry(self.dialog_frame2, textvariable = self.option3, width=45).place(x=30, y=100)

		self.b4 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 4).place(x=5, y = 130)
		self.option4 = tk.StringVar()
		self.input4 = tk.Entry(self.dialog_frame2, textvariable = self.option4, width=45).place(x=30, y=130)

		self.b5 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 5).place(x=5, y = 160)
		self.option5 = tk.StringVar()
		self.input5 = tk.Entry(self.dialog_frame2, textvariable = self.option5, width=45).place(x=30, y=160)

		# self.answer_label = tk.Label(self.dialog_frame2, text = 'Answer(A)').place(x=275, y=160)
		# self.answer = tk.StringVar()
		# self.answer_input = tk.Entry(self.dialog_frame2, textvariable = self.answer, width=5).place(x=345, y=160)

		self.done_button = tk.Button(self.button_frame, text = 'DONE', command = self.question_get)
		self.done_button.pack(side = tk.LEFT)

		self.Back_button = tk.Button(self.button_frame, text='BACK', command = self.question_back)
		self.Back_button.pack(side = tk.LEFT)


	def open_edit_radio(self):
		'''
		Show radio button with all data of the question that is already made when a user wants to edit the question
		'''
		self.add_button.destroy()
		self.edit_button.destroy()
		self.delete_button.destroy()
		self.create_quiz_button.destroy()
		self.scrollbar_2.destroy()
		self.radio_area.destroy()

		self.problem_label = tk.Label(self.dialog_frame2, text = 'Question').place(x = 10, y = 5)
		self.q_content = tk.StringVar(self.dialog_frame2, value = self.current_question['question'])
		self.problem = tk.Entry(self.dialog_frame2, textvariable = self.q_content, width = 30)
		self.problem.place(x=70, y=5)

		# get correct answer
		num_b = {'A' : 1, 'B' : 2, 'C' : 3, 'D' : 4, 'E' : 5}
		ans = self.current_question['answer']

		#Radio Buttons
		self.term = tk.IntVar()
		if ans:
			self.term.set(num_b[ans])
		self.b1 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 1).place(x=5, y = 40)
		self.option1 = tk.StringVar(self.dialog_frame2, value = self.current_question['A'])
		self.input1 = tk.Entry(self.dialog_frame2, textvariable = self.option1, width=45).place(x=30, y=40)

		self.b2 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 2).place(x=5, y = 70)
		self.option2 = tk.StringVar(self.dialog_frame2, value = self.current_question['B'])
		self.input2 = tk.Entry(self.dialog_frame2, textvariable = self.option2, width=45).place(x=30, y=70)

		self.b3 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 3).place(x=5, y = 100)
		self.option3 = tk.StringVar(self.dialog_frame2, value = self.current_question['C'])
		self.input3 = tk.Entry(self.dialog_frame2, textvariable = self.option3, width=45).place(x=30, y=100)

		self.b4 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 4).place(x=5, y = 130)
		self.option4 = tk.StringVar(self.dialog_frame2, value = self.current_question['D'])
		self.input4 = tk.Entry(self.dialog_frame2, textvariable = self.option4, width=45).place(x=30, y=130)

		self.b5 = tk.Radiobutton(self.dialog_frame2, variable=self.term, value = 5).place(x=5, y = 160)
		self.option5 = tk.StringVar(self.dialog_frame2, value = self.current_question['E'])
		self.input5 = tk.Entry(self.dialog_frame2, textvariable = self.option5, width=45).place(x=30, y=160)

		#Change and Back buttons
		self.done_button = tk.Button(self.button_frame, text = 'CHANGE', command = self.question_change_get)
		self.done_button.pack(side = tk.LEFT)

		self.Back_button = tk.Button(self.button_frame, text='BACK', command = self.open_edit_question_back)
		self.Back_button.pack(side = tk.LEFT)

	def question_get(self):
		'''if user creates a question and clicks DONE button, 
		question_get(self) is called. It destroys old frames and display the list of questions
		'''
		ans_dict = {1 : "A", 2 : "B", 3 : "C", 4 : "D", 5 : "E"}
		a = self.term.get()
		q = self.q_content.get()
		A = self.option1.get()
		B = self.option2.get()
		C = self.option3.get()
		D = self.option4.get()
		E = self.option5.get()
		if q and a and A and B and C and D and E:
			answer = ans_dict[a]
			dict_qe = self.dict_question(answer, q, A, B, C, D, E)
			self.qe_list.append(dict_qe)
			self.temp_qe_list = self.qe_list
			messagebox.showinfo("Create Question", "Finish create a question.")
			self.dialog_frame2.destroy()
			self.button_frame.destroy()
			self.done_button.destroy()
			self.Back_button.destroy()
			if (self.edit == False):
				self.question_frame()
			else:
				self.open_question_frame()
			for i in range(len(self.temp_qe_list)):
				self.radio_area.insert(tk.END, "Question "+str(i+1)+" :"+self.temp_qe_list[i]['question'])
		else:
			if not q:
				messagebox.showerror("Input Error", "Please input question.")
			elif not A or not B or not C or not D or not E:
				messagebox.showerror("Input Error", "Please input all answer options.")
			elif not a:
				messagebox.showerror("Input Error", "Please select a correct answer.")

	def question_back(self):
		'''
		Destroy old frame and display list of questions
		'''
		self.dialog_frame2.destroy()
		self.button_frame.destroy()
		self.done_button.destroy()
		self.Back_button.destroy()
		self.open_question_frame()
		for i in range(len(self.qe_list)):
			self.radio_area.insert(tk.END, "Question "+str(i+1)+" :"+self.qe_list[i]['question'])

	def open_edit_question_back(self):
		'''
		Destroy old frame and display new list of edited questions
		'''
		self.dialog_frame2.destroy()
		self.button_frame.destroy()
		self.done_button.destroy()
		self.Back_button.destroy()
		self.open_question_frame()
		for i in range(len(self.qe_list)):
			self.radio_area.insert(tk.END, "Question "+str(i+1)+" :"+self.qe_list[i]['question'])

	def get_quiz(self):
		self.quizList = []
		self.quiz_list.bind('<<ListboxSelect>>', self.selected_quiz)

	def selected_quiz(self, evt):
		'''
		When quiz is selected, insert into list, if not prints error
		'''
		try:
			w = evt.widget
			index = int(w.curselection()[0])
			value = self.qu_list[index]
			self.current_quiz = value
		except IndexError as e:
			print("No QUIZES")
			pass

	def selected_question(self, evt):
		'''
		When question is selected, insert into list if not, prints error
		'''
		try:
			w = evt.widget
			index = int(w.curselection()[0])
			question = self.qe_list[index]
			self.current_question = question
			print(self.current_question)
		except IndexError as e:
			self.current_question = None
			print("No QUESTION")
			pass

	def send_quit_msg(self):
		'''
		When user quits application, send the dictionary to identify the connection of teacher and student
		'''
		d = {"type": CONN, "OP": "quit"}
		self.broadcast(d)

	def quit(self):
		'''
		Application is closed
		'''
		if messagebox.askyesno("Close Prompt", "Are you sure you want to quit?"):
			self.build_report()
			self.send_quit_msg()
			self.quitting = True
			for client in self.clients:
				client.close()
				#client.shutdown(socket.SHUT_WR)
			self.server.close()
			root.quit()
			sys.exit(0)

	def closeWin(self):
		messagebox.showinfo("Close Window", "Please logout your account.")


	def build_report(self):
		current_time = datetime.datetime.now()
		filename = "answers/session-" + current_time.strftime("%H:%M:%S-%B-%d-%Y") + ".txt"
		with open(filename, "w") as f:
			q_table = {}
			for item in self.qu_list:
				#q_table[item['hash']] = item['name']
				q_table[item['hash']] = { i['hash']:i['answer'] for i in item['questions']}
				print(q_table)
			if self.answer_list:
				for item in self.answer_list:
					f.write("Student Name: " + item['name'] + "\n\n")
					right = 0
					total = 0
					for ans in item['answers']:
						total += 1
						f.write("Question " + str(total) + ": \n")
						if ans['ans'] == q_table[item['hash']][ans['hash']]:
							f.write("CORRECT\n\n")
							right += 1
						else:
							f.write("INCORRECT\n\n")
					f.write("Result: " + str(right) + "/" + str(total) + "\n")
					f.write("-------------------------------------------------\n")
					f.write("\n")

			else:
				f.write("No Answers Recieved For this Session")

	'''
	Begin file io functions
	'''
	def create_quiz_file(self, quiz):
		filename = "quizes/" + quiz['name'] + ".qz"
		p_quiz = pickle.dumps(quiz)
		with open(filename, "wb") as f:
			f.write(p_quiz)
		# print("Wrote to file")

	def load_quiz_file(self, filename):
		try:
			with open("quizes/" + filename, "rb") as f:
				p_quiz = f.read()
				quiz = pickle.loads(p_quiz)
				#print(quiz)
			return quiz
		except Exception as e:
			print("Error ins load quiz")




def main():
	try:
		global root
		root = tk.Tk()
		app = Main_View(root)
		root.mainloop()
	except Exception as e:
		print("Your operating system is blocking the program from using port 44000.")
		print("Wait about half a minute and try again.")

if __name__ == '__main__':
	main()
	