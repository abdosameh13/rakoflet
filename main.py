import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image as KivyImage
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
from PIL import Image
import qrcode
from pyzbar.pyzbar import decode
import pyperclip
import os

class QRApp(App):
    def build(self):
        self.mode = "main"
        self.camera_reading = False
        self.encryption_key = 42  # Encryption key (can be changed)

        # Create main layout
        self.layout = BoxLayout(orientation='vertical')

        # Create display area
        self.display_image = KivyImage()
        self.layout.add_widget(self.display_image)

        # Create control frame for main mode
        self.button_layout = BoxLayout(orientation='horizontal')
        self.layout.add_widget(self.button_layout)

        # Main mode buttons
        self.read_camera_button = Button(text="Read QR from Camera")
        self.read_camera_button.bind(on_press=self.start_camera_read)
        self.button_layout.add_widget(self.read_camera_button)

        self.read_image_button = Button(text="Read QR from Image")
        self.read_image_button.bind(on_press=self.read_qr_image_ui)
        self.button_layout.add_widget(self.read_image_button)

        self.generate_button = Button(text="Generate QR Code")
        self.generate_button.bind(on_press=self.switch_to_generate_mode)
        self.button_layout.add_widget(self.generate_button)

        # Attempt to open the camera
        self.cap = cv2.VideoCapture(0)
        self.has_camera = self.cap.isOpened()
        if self.mode == "main":
            Clock.schedule_interval(self.update_video, 1.0 / 30.0)

        return self.layout

    def update_video(self, dt):
        if self.mode != "main":
            return
        if self.has_camera and self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                if self.camera_reading:
                    codes = decode(frame)
                    if codes:
                        for code in codes:
                            text = code.data.decode('utf-8')
                            self.handle_qr_text(text)
                            self.camera_reading = False
                            break
                # Convert frame to texture for display in Kivy
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.display_image.texture = texture
            else:
                self.display_image.texture = None
        else:
            self.display_image.texture = None

    def handle_qr_text(self, text):
        # Decrypt the text
        decrypted_text = xor_encrypt_decrypt(text, self.encryption_key)
        pyperclip.copy(decrypted_text)
        # Display message
        self.display_image.texture = None
        self.layout.add_widget(Label(text="QR code read successfully"))

    def start_camera_read(self, instance):
        if not self.has_camera:
            self.layout.add_widget(Label(text="No Camera Found"))
            return
        self.camera_reading = True

    def read_qr_image_ui(self, instance):
        # On mobile, you can use filechooser or similar to select the image
        # Here we assume a fixed path for simplicity
        file_path = "path/to/image.png"  # This should be adjusted for mobile
        if file_path and os.path.exists(file_path):
            img = cv2.imread(file_path)
            if img is None:
                self.layout.add_widget(Label(text="Failed to read image"))
                return
            codes = decode(img)
            if codes:
                for code in codes:
                    text = code.data.decode('utf-8')
                    self.handle_qr_text(text)
                    break
            else:
                self.layout.add_widget(Label(text="No QR code found in the image"))
            # Display the image
            buf = cv2.flip(img, 0).tobytes()
            texture = Texture.create(size=(img.shape[1], img.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.display_image.texture = texture

    def switch_to_generate_mode(self, instance):
        self.mode = "generate"
        if self.has_camera and self.cap is not None:
            self.cap.release()
            self.cap = None
        # Create new layout for generating QR
        self.generate_layout = BoxLayout(orientation='vertical')
        self.layout.add_widget(self.generate_layout)

        label = Label(text="Enter text:")
        self.generate_layout.add_widget(label)

        self.text_entry = TextInput(multiline=False)
        self.generate_layout.add_widget(self.text_entry)

        self.gen_confirm_button = Button(text="Generate")
        self.gen_confirm_button.bind(on_press=self.generate_qr_ui)
        self.generate_layout.add_widget(self.gen_confirm_button)

        self.back_button = Button(text="Back")
        self.back_button.bind(on_press=self.back_to_main)
        self.generate_layout.add_widget(self.back_button)

    def generate_qr_ui(self, instance):
        text = self.text_entry.text
        if not text:
            self.layout.add_widget(Label(text="Please enter text"))
            return
        # Encrypt the text
        encrypted_text = xor_encrypt_decrypt(text, self.encryption_key)
        qr_img = qrcode.make(encrypted_text)
        qr_img = qr_img.resize((300, 300))
        # Save the image temporarily for display
        temp_file = "temp_qr.png"
        qr_img.save(temp_file)
        self.display_image.source = temp_file
        self.display_image.reload()
        # You can add an option to save the image to the gallery on the phone

    def back_to_main(self, instance):
        self.mode = "main"
        self.layout.remove_widget(self.generate_layout)
        self.cap = cv2.VideoCapture(0)
        self.has_camera = self.cap.isOpened()
        Clock.schedule_interval(self.update_video, 1.0 / 30.0)

def xor_encrypt_decrypt(text, key):
    return ''.join(chr(ord(c) ^ key) for c in text)

if __name__ == "__main__":
    QRApp().run()
