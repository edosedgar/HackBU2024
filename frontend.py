import gradio as gr
import time
import twitter
import encoder
import llm

def retr_msg_func(i, cur_prob, msg):
    n = len(msg)
    if i >= n:
        return -1
    return msg[i]

def bruteforce_decode(decoded_stream, password):
    for i in range(len(decoded_stream)):
        for wind_len in range(64, 64*6+1, 16):
            try:
                extr_msg = encoder.decode(decoded_stream[i:i + wind_len], password, mode='2bit')
                return extr_msg
            except:
                continue
    return -1

#model_name = 'gpt2'
model_name = "tiiuae/falcon-7b"

model = llm.LMHeadModel(model_name)
model.set_params(top_k=4, temp=0.4, rep_pen=1.1)

def encoder_func(prompt, message, password):
    if len(prompt) < 10 or len(password) == 0 or len(message) == 0:
        return ""
    msg = encoder.encode(message, password, mode='2bit')
    print('ENCODER>>', 'secret message length:', len(message), ', num tokens used:', len(msg))
    print('ENCODER>>', "encrypted msg:", msg)
    print('ENCODER>>', "prompt:", prompt)
    enc_txt = model.encode_message(prompt, retr_msg_func=retr_msg_func, msg=msg)
    print('ENCODER>>', "generated:", enc_txt)
    return enc_txt

def decoder_func(encoded_str, password):
    if len(encoded_str) == 0 or len(password) == 0:
        return ""
    restored_stream = model.decode_message(encoded_str)
    print('DECODER>>', restored_stream)
    dec_str = bruteforce_decode(restored_stream, password)
    if dec_str == -1:
        return "## Could not extract message! ##"
    return dec_str

def post_func(encoded_str):
    if len(encoded_str) == 0:
        return
    twitter.post_text(encoded_str)
    time.sleep(2)
    return

with gr.Blocks(title='SecretGPT') as demo:
    gr.Markdown("Communicate secretly on social media with LLM")
    with gr.Tab("Encoder"):
        text_input1 = gr.Textbox(label='Prompt (at least a few words)')
        text_input2 = gr.Textbox(label='Message (more words take more time)')
        text_input3 = gr.Textbox(label='Password')
        text_button1 = gr.Button("Encode with " + model_name.split('/')[-1])
        text_output = gr.Textbox(label='Encoded message', interactive=False)
        text_button2 = gr.Button("Post to SecretGPT Twitter 💃💃💃")

        text_button1.click(encoder_func, inputs=[text_input1, text_input2, text_input3], outputs=[text_output])
        text_button2.click(post_func, inputs=[text_output])

    with gr.Tab("Decoder"):
        text_input1 = gr.Textbox(label='Encoded message')
        text_input2 = gr.Textbox(label='Password')
        text_button = gr.Button("Decode")
        text_output = gr.Textbox(label='Decoded message', interactive=False)

        text_button.click(decoder_func, inputs=[text_input1, text_input2], outputs=[text_output])

#demo.launch(server_name='0.0.0.0', share=True)
demo.launch(server_name='0.0.0.0')