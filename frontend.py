import gradio as gr
import time
import twitter
import encoder
import llm
import datetime

MAX_LIMIT = 50

def gettime():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime('%H:%M:%S')
    return formatted_time

def retr_msg_func(i, cur_prob, msg):
    n = len(msg)
    if i >= n:
        return -1
    return msg[i]

def bruteforce_decode(decoded_stream, password):
    for i in range(len(decoded_stream)):
        rem_len = len(decoded_stream) - i
        for wind_len in reversed(range(64, (rem_len//64)*64+1, 16)):
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
    message = message[:MAX_LIMIT]
    print(f'ENCODER {gettime()} >>', "prompt:", prompt)
    msg = encoder.encode(message, password, mode='2bit')
    print(f'ENCODER {gettime()} >>', 'secret message length (bytes):', len(message))
    print(f'ENCODER {gettime()} >>', 'encrypted message length (tokens):', len(msg))
    print(f'ENCODER {gettime()} >>', "encrypted message:", msg)
    enc_txt = model.encode_message(prompt, retr_msg_func=retr_msg_func, msg=msg)
    print(f'ENCODER {gettime()} >>', "generated:", enc_txt)
    return enc_txt

def decoder_func(encoded_str, password):
    if len(encoded_str) == 0 or len(password) == 0:
        return ""
    restored_stream = model.decode_message(encoded_str)
    print(f'DECODER {gettime()} >>', "extracted encrypted message:", restored_stream)
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

def control_length(input_str):
    #print(input_str)
    return f'{len(input_str)}/{MAX_LIMIT} used'

with gr.Blocks(title='SecretGPT') as demo:
    gr.Markdown("Communicate secretly on social media with LLM")
    with gr.Tab("Encoder"):
        text_input1 = gr.Textbox(label='Prompt (at least a few words, keep it open-ended)')
        text_input2 = gr.Textbox(label=f'Message (max {MAX_LIMIT} characters)', max_lines=1)
        text_output0 = gr.Label(show_label=False, value=f'0/{MAX_LIMIT} used')
        text_input3 = gr.Textbox(label='Password', max_lines=1, type='password')
        text_button1 = gr.Button("Encode with " + model_name.split('/')[-1])
        text_output = gr.Textbox(label='Encoded message', interactive=False, show_copy_button=True)
        with gr.Row():
            text_button2 = gr.Button("Post to SecretGPT Twitter 💃💃💃")
            text_button3 = gr.Button("Go to SecretGPT Twitter (new tab)", link='https://twitter.com/GptSecret56909')

        text_button1.click(encoder_func, inputs=[text_input1, text_input2, text_input3], outputs=[text_output],\
                           queue=False, trigger_mode='once')
        text_button2.click(post_func, inputs=[text_output], queue=False, trigger_mode='once')

        text_input2.input(fn = control_length, inputs = [text_input2], outputs = [text_output0], queue=True,\
                          show_progress='hidden', trigger_mode='always_last', concurrency_limit=1)

    with gr.Tab("Decoder"):
        text_input1 = gr.Textbox(label='Encoded message')
        text_input2 = gr.Textbox(label='Password', max_lines=1, type='password')
        text_button = gr.Button("Decode")
        text_output = gr.Textbox(label='Decoded message', interactive=False)

        text_button.click(decoder_func, inputs=[text_input1, text_input2], outputs=[text_output],\
                          queue=False, trigger_mode='once')

demo.launch(server_name='0.0.0.0', share=True)
#demo.launch(server_name='0.0.0.0')