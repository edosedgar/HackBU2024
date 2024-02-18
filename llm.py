import numpy as np
import torch

from transformers import pipeline
from transformers import AutoModelForCausalLM , AutoTokenizer
from transformers import LogitsProcessorList, TopKLogitsWarper,TemperatureLogitsWarper, RepetitionPenaltyLogitsProcessor, NoBadWordsLogitsProcessor

# Classes required to work with LLMs
torch.backends.cuda.matmul.allow_tf32 = True

class BeamSearchNode:
    def __init__(self, sequence, score):
        self.sequence = sequence
        self.score = score

class LMHeadModel:

    def __init__(self, model_name):
        # Initialize the model and the tokenizer.
        self.model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto', torch_dtype=torch.float16)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, decode_with_prefix_space=True)
        self.pad_token = self.tokenizer.eos_token
        self.set_params(top_k=5, temp=1.0, rep_pen=1.0)

    def set_params(self, top_k=5, temp=1.0, rep_pen=1.0):
        self.top_k = top_k
        ## To avoid non-sense
        bad_words = self.tokenizer(['\n', '\n\n'] + self.tokenizer.all_special_tokens, add_special_tokens=True).input_ids

        self.logits_processor = LogitsProcessorList(
        [
            ## fool no bad word processor to avoid generating end of text
            NoBadWordsLogitsProcessor(bad_words_ids=bad_words, eos_token_id=100000),
            TemperatureLogitsWarper(temperature=temp),
            TopKLogitsWarper(top_k=top_k),
            RepetitionPenaltyLogitsProcessor(penalty=rep_pen)
        ])

    def next_word(self, sentence):
        with torch.no_grad():
            input_ids = self.tokenizer.encode(sentence, return_tensors="pt")
            logits = self.model(input_ids).logits[:, -1, :].float()
        logits = self.logits_processor(input_ids, logits)

        # Get the token probabilities for all candidates.
        probs = torch.nn.functional.softmax(logits, dim=-1)
        topk = torch.topk(probs, self.top_k)
        probs, positions = topk[0].tolist()[0], topk[1].tolist()[0]

        # Decode the top k candidates back to words.
        topk_candidates_tokens = \
            [self.tokenizer.decode([idx], add_special_tokens=False) for idx in positions]

        # Return the top k candidates and their probabilities.
        return [topk_candidates_tokens, positions, probs]

    def next_words(self, sentence, max_words=2):
        beam = [BeamSearchNode([sentence], 1.0)]

        for _ in range(max_words):
            candidates = []
            for node in beam:
                tokens, _, probs = self.next_word("".join(node.sequence))
                for token, prob in zip(tokens, probs):
                    new_seq = node.sequence + [token]
                    new_score = node.score * prob
                    candidates.append(BeamSearchNode(new_seq, new_score))

            beam = candidates

        beam = sorted(beam, key=lambda x: x.score, reverse=True)
        words, prob = list(zip(*[(node.sequence, node.score) for node in beam]))
        return words, prob

    def encode_message(self, prompt, retr_msg_func, msg):
        context = prompt
        pos = 0
        while True:
            tokens, _, probs = self.next_word(context)
            idx = retr_msg_func(pos, probs, msg)
            #print(idx, tokens[idx])
            if idx != -1:
                context = context + tokens[idx]
                pos += 1
            else:
                # TODO: what if it is ! or ?
                if any([token == '.' for token in tokens]):
                    context = context + '.'
                    break
                else:
                    context = context + tokens[np.argmax(probs)]
        return context

    def decode_message(self, encoded_msg):
        tokens_ids = self.tokenizer.encode(encoded_msg, return_tensors='np')[0]
        decoded_msg = []

        for i in range(1, len(tokens_ids)-1):
            trunc_enc_msg = "".join([self.tokenizer.decode(idx, add_special_tokens=False) for idx in tokens_ids[:i]])
            #print(trunc_enc_msg)
            _, ids, _ = self.next_word(trunc_enc_msg)
            found_idx = -1
            for j, id in enumerate(ids):
                if id == tokens_ids[i]:
                    found_idx = j
            decoded_msg.append(found_idx)

        return decoded_msg