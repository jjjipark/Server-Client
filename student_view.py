import sys
import tkinter as tk
from tkinter import messagebox

from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import pickle







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


name = ''

class Main_View:
	def __init__(self, main):
		'''
		Initialize the class for student view
		'''
		self.main = main
		self.main.title('Main')
		# call function to open student view window
		self.student_window()
		# fix the window height and width that user cannot change
		self.main.resizable(False, False)

	def student_window(self):
		'''
		Set-up student log in window by create label and input entries of
		'Name' and 'IP Address'. Also create a button 'OK' which student can
		log in to application.
		'''
		self.Name_Label = tk.Label(self.main, text = 'Student ID')
		self.Name_Label.grid(row=0, column = 0)
		self.Name_Label.pack()

		self.my_id = tk.StringVar()
		self.Name_Input = tk.Entry(self.main, textvariable = self.my_id)
		self.Name_Input.grid(row=0, column = 1)
		self.Name_Input.pack()

		self.IP_Label = tk.Label(self.main, text = 'IP Address')
		self.IP_Label.grid(row = 1, column = 0)
		self.IP_Label.pack()

		self.my_ip = tk.StringVar()
		self.IP_Input = tk.Entry(self.main, textvariable = self.my_ip)
		self.IP_Input.grid(row = 1, column =1)
		self.IP_Input.pack()

		self.ok_button = tk.Button(self.main, text = 'OK', command = self.student_view)
		self.ok_button.grid(row = 2, column = 0, columnspan = 2)
		self.ok_button.pack(side = tk.LEFT, expand = True)


	def student_view(self):
		global name 							#Create name variable containing teacher_name to be global
		global ip_addr
		if(self.my_id.get() and self.my_ip.get()):
			name = self.my_id.get()
			ip_addr = self.my_ip.get()
			# get ID and IP address input and connect web server
			try:
				self.addr = (ip_addr, PORT)
				self.client_socket = socket(AF_INET, SOCK_STREAM)
				self.client_socket.settimeout(1)
				self.client_socket.connect(self.addr)
				# call Student_View class to open application
				self.t_app = Student_View(self.main, self.client_socket)
				self.Name_Label.destroy()
				self.Name_Input.destroy()
				self.IP_Label.destroy()
				self.IP_Input.destroy()
				self.ok_button.destroy()
			except Exception as e:
				messagebox.showinfo("Connection", "There is no teacher currently hosting at this IP Address, try again")
		else:
			# pop-up message to hint user
			if not self.my_id.get():
				messagebox.showerror("Error", "Please enter name!")
			if not self.my_ip.get():
				messagebox.showerror("Error", "Please enter IP address!")

class Student_View:
	def __init__(self, student, socket):
		'''
		BEGIN NETWORK SET UP
		'''
		self.bufsiz = 4096
		self.addr = (ip_addr, 44000)
		self.client_socket = socket
		self.client_socket.settimeout(None)
		self.connected = True


		d = {"type": CONN, "name": name}
		m = pickle.dumps(d)

		self.client_socket.send(m)
		self.receive_thread = Thread(target=self.receive)
		self.receive_thread.start()
		'''
		END NETWORK SET UP
		'''

		self.student = student
		self.student.title("Student")
		self.student.resizable(False, False)

		self.init_dialog()
		self.init_quizFrame()
		# initialize lists to store quizes, questions, answers, and hash values
		self.current_quiz = None
		self.current_question = None
		self.viewing_question = False
		self.quizes = []
		self.quiz_hashes = []
		self.quiz_answers = []
		# control cross button to close window
		self.student.protocol('WM_DELETE_WINDOW', self.closeWin)

	def send(self, message: str) -> None:

		d = {"type": MSG, "msg": message, "name": message}
		m = pickle.dumps(d)
		self.client_socket.send(m)

	def dict_ans(self, answer: str, h: "Hash")  -> dict:
		# create a answer dictionary to store answer, hash value, and question name
		d = {"type": ANSWER, "ans": answer, "hash": h, "name": name}
		return d;

	def send_answers(self) -> None:
		# determine quiz_answers list has answer
		if self.quiz_answers:
			# send the dictionary to server
			d = {'type': ANSWERS, 'name':name}
			d['hash'] = self.current_quiz['hash']
			d['answers'] = self.quiz_answers
			m = pickle.dumps(d)
			self.client_socket.send(m)
			# after send, clear the list
			self.quiz_answers = []

	def receive(self) -> None:
		while True:
			try:
				msg = self.client_socket.recv(self.bufsiz)
				d = pickle.loads(msg)
				# when received type is QUIZ
				if d["type"] == QUIZ:
					if d["hash"] not in self.quiz_hashes:
						# add quiz into list
						self.quiz_hashes.append(d["hash"])
						self.quizes.append(d)
						self.quiz_list.insert(tk.END, d["name"])
				# when received type is CONN
				elif d["type"] == CONN:
					self.client_socket.close()
					self.quit(teacher_quit = True)
					return
				else:
					print("unimplemented message type")
					print(d)
			except OSError:
				break

	def init_dialog(self, NoLogOut = False) -> None:
		'''
		Create student user interface by added a send message entry and show quiz
		list box that students can receive quizes teacher assigned.
		'''
		global name

		if not NoLogOut:
			self.Main_Frame_S = tk.Frame(self.student, height = 30, width = 100)
			self.Main_Frame_S.grid(row=0, column=0)
			self.Main_Frame_S.pack()

			# show student name
			self.showname = tk.Label(self.Main_Frame_S, text=name).grid(row=0, column=0, sticky = tk.W)
			self.log_outButton = tk.Button(self.Main_Frame_S, text="LOGOUT", command = self.quit).grid(row=0, column=1, sticky = tk.E)

		# Message dialog frame
		self.messages_frame = tk.Frame(self.student, relief = tk.RAISED, borderwidth = 1)
		self.messages_frame.grid(row = 0, column = 0, padx = 0, pady =0)
		self.messages_frame.pack(side = tk.LEFT,fill=tk.Y)

		self.dialog_frame = tk.Frame(self.messages_frame, height = 20, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.dialog_frame.grid(row=0, column=0)
		self.dialog_frame.pack()

		# scrollbar for dialog
		self.scrollbar_1 = tk.Scrollbar(self.dialog_frame, orient = tk.VERTICAL)
		self.scrollbar_1.pack(side=tk.RIGHT, fill=tk.Y)

		self.quiz_list = tk.Listbox(self.dialog_frame, height=20, width=50, yscrollcommand=self.scrollbar_1.set)
		self.quiz_list.grid(row=0, column = 1)
		self.quiz_list.pack()

		self.scrollbar_1.config(command = self.quiz_list.yview)
		# by click button BEGIN, to start the quiz
		self.send_button = tk.Button(self.messages_frame, text="BEGIN", width=48, command=self.quiz_window)
		self.send_button.pack(side = tk.LEFT, expand = True)
		self.quiz_list.bind('<<ListboxSelect>>', self.selected_quiz)

	def quiz_window(self) -> None:
		# call quiz window
		if not self.current_quiz:
			messagebox.showinfo("Invalid Input", "Please select a quiz.")
			return
		self.messages_frame.destroy()
		self.make_quiz()


	def selected_quiz(self, evt):
		# command function for listbox bind method
		try:
			w = evt.widget
			index = int(w.curselection()[0])
			value = self.quizes[index]
			self.current_quiz = value
		except IndexError as e:
			self.current_quiz = None
			pass

	def make_quiz(self):
		# QUESTIONABLE
		self.quiz_list.destroy()

		self.quiz_frame = tk.Frame(self.student, relief = tk.RAISED, borderwidth = 1)
		self.quiz_frame.grid(row = 0, column = 0, padx = 0, pady =0)
		self.quiz_frame.pack(side = tk.LEFT,fill=tk.Y)

		self.dialog_frame = tk.Frame(self.quiz_frame, height = 20, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.dialog_frame.grid(row=0, column=0)
		self.dialog_frame.pack()

		# scrollbar for dialog
		self.scrollbar_2 = tk.Scrollbar(self.dialog_frame, orient = tk.VERTICAL)
		self.scrollbar_2.pack(side=tk.RIGHT, fill=tk.Y)

		self.question_list = tk.Listbox(self.dialog_frame, height=20, width=50, yscrollcommand=self.scrollbar_2.set)
		self.question_list.grid(row=0, column = 1)
		self.question_list.pack()

		self.scrollbar_2.config(command = self.question_list.yview)
		# button can quit the quiz
		self.stop_button = tk.Button(self.quiz_frame, text="STOP", command = self.quiz_stop)
		self.stop_button.pack(side = tk.LEFT, expand = True)
		# button can submit quiz questions' answers
		self.submit_button = tk.Button(self.quiz_frame, text="SUBMIT", command = self.quiz_submit)
		self.submit_button.pack(side = tk.RIGHT, expand = True)

		open_quiz = self.current_quiz
		# put questions of quiz into list box to show all questions contained in the quiz
		for question in open_quiz['questions']:
			self.question_list.insert(tk.END, question['question'])

		# select a question from the list
		self.question_list.bind('<<ListboxSelect>>', self.selected_question)


	def quiz_submit(self):
		if messagebox.askyesno("Submit Prompt", "Are you sure you want to Submit?"):
			if self.viewing_question and self.term.get():
				# store answers that students answered
				ans_dict = {0: "Shouldn't pick this", 1 : "A", 2 : "B", 3 : "C", 4 : "D", 5 : "E"}
				ans = self.dict_ans(ans_dict[self.term.get()], self.current_question['hash'])
				replace = False
				for index, item in enumerate(self.quiz_answers):
					if item['hash'] == ans['hash']:
						self.quiz_answers[index] = ans
						replace = True
				if not replace:
					self.quiz_answers.append(ans)
			# if current quiz contain quiz, send the quiz answer to server
			if self.current_quiz:
				self.send_answers()
				self.quizes.remove(self.current_quiz)
				self.quiz_hashes.remove(self.current_quiz['hash'])
				# after sent, clear the list
				self.current_quiz = None

			self.quiz_frame.destroy()
			self.dialog_frame.destroy()
			self.scrollbar_2.destroy()
			self.question_list.destroy()
			self.stop_button.destroy()
			self.submit_button.destroy()

			if self.viewing_question:
				self.canvas_frame.destroy()
				self.question_text.destroy()
				self.viewing_question = False
			# back to student view interface
			self.init_dialog(True)
			# show quizes are not submit
			for d in self.quizes:
				self.quiz_list.insert(tk.END, d["name"])


	def quiz_stop(self) -> None:
		'''
		command function for STOP button
		'''
		if messagebox.askyesno("Stop Prompt", "Are you sure you want to Stop? If so, quiz will be forfeited."):
			if self.current_quiz:
				# remove the quiz data from dictionary
				self.quiz_answers = []
				self.quizes.remove(self.current_quiz)
				self.quiz_hashes.remove(self.current_quiz['hash'])
				self.current_quiz = None
			# back to student view interface
			self.quiz_frame.destroy()
			self.dialog_frame.destroy()
			self.scrollbar_2.destroy()
			self.question_list.destroy()
			self.stop_button.destroy()
			self.submit_button.destroy()
			if self.viewing_question:
				self.canvas_frame.destroy()
				self.question_text.destroy()
				self.viewing_question = False

			self.init_dialog(True)
			# show quizes are not started
			for d in self.quizes:
				self.quiz_list.insert(tk.END, d["name"])


	def init_quizFrame(self) -> None:
		self.quiz_frame = tk.Frame(self.student, relief= tk.RAISED, borderwidth = 1)
		self.quiz_frame.grid(row = 0, column = 0, padx = 0, pady = 0)
		self.quiz_frame.pack(side = tk.RIGHT, fill = tk.Y)

		self.showquiz_frame = tk.Frame(self.quiz_frame, height = 20, width = 50, relief = tk.RAISED, borderwidth = 1)
		self.showquiz_frame.grid(row=0, column=0)
		self.showquiz_frame.pack()

		# create canvas on the frame
		self.canvas = tk.Canvas(self.showquiz_frame, width = 455, height = 340, borderwidth = 1, scrollregion = (0, 0, 500, 800), highlightthickness = 0)
		self.canvas.grid_propagate(False)
		self.canvas.grid(row=0, column=0)
		self.canvas.pack(side = tk.LEFT, expand = tk.YES, fill = tk.BOTH)

		# inset scrollbar on canvas
		self.scrollbar_2 = tk.Scrollbar(self.showquiz_frame, orient = tk.VERTICAL)
		self.scrollbar_2['command'] = self.canvas.yview
		self.canvas['yscrollcommand'] = self.scrollbar_2.set
		self.scrollbar_2.pack(side = tk.RIGHT, fill = tk.Y)
		# students can send message through the Text
		self.entry_field = tk.Text(self.quiz_frame, width=57, height=2, highlightthickness=1, highlightbackground="Black", highlightcolor="Light Blue")
		self.entry_field.insert(tk.END, "Type your messages here.")
		self.entry_field.pack(side = tk.LEFT, expand = True)
		# click Send button to send message to teacher
		self.send_button = tk.Button(self.quiz_frame, text="Send", command=self.send_msg)
		self.send_button.pack(side = tk.LEFT, expand = True)

	def send_msg(self) -> None:
		'''
		command function of Send button
		'''
		self.get_msg = self.entry_field.get("1.0", 'end-1c')
		if self.get_msg == "Type your messages here.":
			messagebox.showinfo("Send Prompt", "Replace the default text")
		elif self.get_msg:
			msg_list = []
			dict_msg = {
					'type' : 2,
					'msg' : self.get_msg
					}
			msg_list.append(dict_msg)
			self.entry_field.delete('1.0', tk.END)
			messagebox.showinfo("Send Prompt", "You successfully sent message.")

			# send message to teacher view
			self.send(self.get_msg)
		else:
			messagebox.showinfo("Send Prompt", "You cannot send empty message.")

	def selected_question(self, evt):
		# catch which question selected, and set the question
		# in to current_question list
		try:
			if self.viewing_question and self.term.get():
				ans_dict = {0: "Shouldn't pick this", 1 : "A", 2 : "B", 3 : "C", 4 : "D", 5 : "E"}
				ans = self.dict_ans(ans_dict[self.term.get()], self.current_question['hash'])
				replace = False
				for index, item in enumerate(self.quiz_answers):
					if item['hash'] == ans['hash']:
						self.quiz_answers[index] = ans
						replace = True
				if not replace:
					self.quiz_answers.append(ans)
				self.canvas_frame.destroy()
				self.question_text.destroy()

			elif self.viewing_question:
				self.canvas_frame.destroy()
				self.question_text.destroy()

			w = evt.widget
			# get index of all questions
			index = int(w.curselection()[0])
			question = self.current_quiz['questions'][index]
			# add question into list
			self.current_question = question
			# call function to show the question in questions list
			self.show_question()
		except IndexError as e:
			self.current_question = None
			pass

	def show_question(self):
		self.viewing_question = True
		# create a frame to contain quiz content
		self.canvas_frame = tk.Frame(self.canvas)
		self.canvas.create_window((0, 0), window=self.canvas_frame, anchor='nw')

		# quiz question test to turn new line
		self.question_text = tk.Label(self.canvas_frame, text = self.current_question['question'], wraplength=450, justify=tk.LEFT)
		self.question_text.grid(row=0, column=0, sticky='w')

		self.term=tk.IntVar()
		# options test to turn new line
		self.b1 = tk.Radiobutton(self.canvas_frame, text=self.current_question['A'], wraplength=400, justify=tk.LEFT, variable=self.term, value=1).grid(row=1, column=0, sticky='w')
		self.b2 = tk.Radiobutton(self.canvas_frame, text=self.current_question['B'], wraplength=400, justify=tk.LEFT, variable=self.term, value=2).grid(row=2, column=0, sticky='w')
		self.b3 = tk.Radiobutton(self.canvas_frame, text=self.current_question['C'], wraplength=400, justify=tk.LEFT, variable=self.term, value=3).grid(row=3, column=0, sticky='w')
		self.b4 = tk.Radiobutton(self.canvas_frame, text=self.current_question['D'], wraplength=400, justify=tk.LEFT, variable=self.term, value=4).grid(row=4, column=0, sticky='w')
		self.b5 = tk.Radiobutton(self.canvas_frame, text=self.current_question['E'], wraplength=400, justify=tk.LEFT, variable=self.term, value=5).grid(row=5, column=0, sticky='w')

	def send_quit_msg(self) -> None:
		# send the message to server when quit
		d = {"type": CONN, "OP": "quit"}
		m = pickle.dumps(d)
		self.client_socket.send(m)

	def quit(self, teacher_quit = False) -> None:
		'''
		A command function to quit the application by click logout button.
		'''
		if teacher_quit:
			messagebox.showinfo("Close Window", "Teacher has ended session")
			root.quit()
			sys.exit(0)
		# a hint for user to ask sure to quit whether or not
		if messagebox.askyesno("Close Prompt", "Are you sure you want to quit?"):
			self.send_quit_msg()
			self.client_socket.close()
			self.student.destroy()
			root.quit()
			sys.exit(0)

	def closeWin(self) -> None:
		'''
		User cannot close window by click cross button upper left
		'''
		messagebox.showinfo("Close Window", "Please logout your account.")


def main():
	try:
		global root
		root = tk.Tk()
		app = Main_View(root)
		root.mainloop()
	except Exception as e:
		print("Your operating system has an issue.")
		print("This application is designed for macOS v10.13.4")

if __name__ == '__main__':
	main()
