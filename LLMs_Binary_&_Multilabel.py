# -*- coding: utf-8 -*-
"""mistral.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1LmpF7JcFJXmlYgfCJUXQiQ19ehYL_r18

# **Dependencies Install**
"""

!which pip
!pip install transformers
!pip install accelerate
!pip install bitsandbytes
!pip install --upgrade transformers

import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import torch
from transformers import AutoTokenizer
from transformers import AutoModelForCausalLM
from transformers import BitsAndBytesConfig
from transformers import StoppingCriteria, StoppingCriteriaList
from tqdm.notebook import tqdm
import sklearn.metrics
from sklearn.metrics import multilabel_confusion_matrix, classification_report
import pprint

# from google.colab import drive
# drive.mount('/content/drive')

import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score



"""#**Skewness of Dataset**"""

cnt = {}
df = pd.read_csv('/content/new.csv')
df = df.sample(frac=1).reset_index(drop=True)
df.head()

non_complaint = (df['Complaint/Non Complaint'] == 0).sum()

print("Total Dataset: ", len(df))
print(f"Number of Complaints are {len(df) - non_complaint}")
print(f"Number of non complaints are {non_complaint}")

value_counts = df['Complaint/Non Complaint'].value_counts()
bar_width =0.2
plt.bar(value_counts.index, value_counts.values, color=['Red', 'Green'], label=['Complaint', 'Non-Complaint'], width=bar_width)
plt.xlabel('Values')
plt.ylabel('Count')
plt.title('Count of Complaints and Non-Complaints')
plt.xticks([0, 1])
plt.legend()
plt.show()

"""# **Number of words Analysis**"""

# pip install nltk

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

nltk.download('punkt')
nltk.download('stopwords')

def clean_and_count_words(text):
    tokens = word_tokenize(text)

    table = str.maketrans('', '', string.punctuation)
    words = [word.lower() for word in tokens if word.isalpha()]
    words = [word.translate(table) for word in words]

    # stop_words = set(stopwords.words('english'))
    # words = [word for word in words if word not in stop_words]
    word_count = len(words)

    return word_count



# Apply the clean_and_count_words function to the 'review' column
df['word_count'] = df['Full Complaint'].apply(clean_and_count_words)

# Display the DataFrame with word counts
print(df)

short_reviews = df[df['word_count'] < 150]
short_reviews = short_reviews.reset_index(drop=True)

short_reviews.to_csv('short_new.csv', index=False)

non_complaint = (short_reviews['Complaint/Non Complaint'] == 0).sum()

print("Total Dataset: ", len(short_reviews))
print(f"Number of Complaints are {len(short_reviews) - non_complaint}")
print(f"Number of non complaints are {non_complaint}")

value_counts = short_reviews['Complaint/Non Complaint'].value_counts()
bar_width =0.2
plt.bar(value_counts.index, value_counts.values, color=['Red', 'Green'], label=['Complaint', 'Non-Complaint'], width=bar_width)
plt.xlabel('Values')
plt.ylabel('Count')
plt.title('Count of Complaints and Non-Complaints')
plt.xticks([0, 1])
plt.legend()
plt.show()

"""# **LLM Model Loading**"""

!pip install peft
!pip install accelerate
!pip install bitsandbytes
!pip install --upgrade transformers

import torch
from transformers import AutoTokenizer
from transformers import AutoModelForCausalLM
from transformers import BitsAndBytesConfig

model_name = "mistralai/Mistral-7B-v0.1"

compute_dtype = getattr(torch, "float16")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=compute_dtype,
    bnb_4bit_use_double_quant=False,
)

access_token = "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"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    quantization_config=bnb_config,
    token=access_token
)

model.config.use_cache = False
model.config.pretraining_tp = 1

tokenizer = AutoTokenizer.from_pretrained(model_name,
                                          trust_remote_code=True,
                                         )
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "left"

device = "cuda:0"

prompt = f"""<<SYS>>Your task is to classify text.

Choose the class among the following classes with the highest probability.
Only return the label in python list, nothing more:

### Classes:
1: 'Complaint'
0: 'Non-Complaint'
<</SYS>>[INST]### Text:
```
Dear Sir /madam,
I am a employee at EENADU journalism college and my wife is admitted at ESIC Nacharam, Hyderabad with a bone breakage in the right elbow on
Saturday evening 22/04/2023 and the condition of the hospital is worst everywhere human waste and employees not taking care of patients there is
no proper response from doctors and today is Wednesday but there is no progress can you please have look into the issue asap
```
[/INST]Label: 1</s><s>[INST]### Text:
```
Good morning sir we are living in chennai ramapuram here nearby miot hospital ramapuram road mgr house road there is one wine shop and
more than 20 infected dogs biting and barking everyone in evening 7to10 time people's get troubled and afraid to come that side kindly please
solve this issue. Women's and childrens were there already we get troubling by drunken guys
```
[/INST]Label : 0</s><s>[INST]### Text:
```

```
[/INST]Label: """.strip()

    encoding = tokenizer(prompt, return_tensors="pt").to(device)
    # print(f"Token length = {len(encoding['input_ids'][0])}",end = ' Label = ')
    with torch.inference_mode():
        outputs = model.generate(
            **encoding,
            top_k = 1,
            max_new_tokens = 2,
            pad_token_id = 2,
            # stopping_criteria=StoppingCriteriaList([StopOnTokens()])
        )

    predict = tokenizer.decode(
        outputs[0][len(encoding['input_ids'][0]):],
        skip_special_tokens=True
    )
    print(predict)

# generation_config = model.generation_config
# generation_config.max_new_tokens = 100                          #Avg length of output generated by model
# generation_config.temperature = 0.08                             #Smaller temp - fact; Larger temp - Creativity to model (Defrines randomness)
# generation_config.top_p = 0.07                                    #top_p - Nuclueus Sampling, takes only (top_p) samples, large- Diverse, small - facts
# generation_config.num_return_sequences = 1
# generation_config.pad_token_id = tokenizer.eos_token_id
# generation_config.eos_token_id = tokenizer.eos_token_id
# generation_config.do_sample = True  # Adjust based on your preference for sampling

# from transformers import StoppingCriteria, StoppingCriteriaList

# class StopOnTokens(StoppingCriteria):
#     def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
#         stop_ids = 2996
#         if ']' in tokenizer.decode(input_ids[0][-1]):
#           return True
#         return False

non_comp = short_reviews[short_reviews['Complaint/Non Complaint']==0]
non_comp = non_comp.reset_index(drop=True)
print("Total number of Non Complaints :", len(non_comp))

non_comp['Full Complaint'][0]



"""# **Zero Shot Binary Classification**"""

prediction = []
i=0

for review in short_reviews['Full Complaint']:
  # %%time
  device = "cuda:0"

  prompt = f"""Your task is to classify text.

  Choose the class among the following classes with the highest probability in a python list.
  Only return the label in python list, nothing more:

   ###Classes###
  'Complaint', 'Non-Complaint'

  For this task, consider the reviews apart from heathcare domain as indicative of 'Non-Complaint.'

        The text to classify:
  ```
  {review}
  ```

  Your response:[
  """.strip()

  encoding = tokenizer(prompt, return_tensors="pt").to(device)
  with torch.inference_mode():
    outputs = model.generate(
        input_ids = encoding.input_ids,
        attention_mask = encoding.attention_mask,
        generation_config = generation_config,
        num_return_sequences=1  # Set this to 1

        stopping_criteria=StoppingCriteriaList([StopOnTokens()])
    )

  predict = tokenizer.decode(outputs[0], skip_special_tokens=True)
  # print(predict)
  response_index = predict.find("Your response:")
  response_label = predict[response_index + len("Your response:"):].strip()
  prediction.append(response_label)
  i=i+1
  print(i)
  print(response_label)

non_comp['Full Complaint'][58]

prediction = [pre.split()[-1] for pre in prediction]

pre_result = [1 if cls == 'Complaint' else 0 for cls in prediction]

conf_matrix = confusion_matrix(short_reviews['Complaint/Non Complaint'], pre_result)

accuracy = accuracy_score(short_reviews['Complaint/Non Complaint'], pre_result)
precision = precision_score(short_reviews['Complaint/Non Complaint'], pre_result)
recall = recall_score(short_reviews['Complaint/Non Complaint'], pre_result)
f1 = f1_score(short_reviews['Complaint/Non Complaint'], pre_result)

# Display the confusion matrix and performance metrics
print("Confusion Matrix:")
print(conf_matrix)
print("\nAccuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1 Score:", f1)

"""# **Few Shot Binary Classification**"""

prediction = []
i=0
from tqdm.notebook import tqdm
for review in tqdm(short_reviews['Full Complaint']):
    # %%time
    device = "cuda:0"

    prompt = f"""<<SYS>>Your task is to classify text.

Choose the class among the following classes with the highest probability.
Only return the label in python list, nothing more:

### Classes:
1: 'Complaint'
0: 'Non-Complaint'
<</SYS>>[INST]### Text:
```
Dear Sir /madam,
I am a employee at EENADU journalism college and my wife is admitted at ESIC Nacharam, Hyderabad with a bone breakage in the right elbow on
Saturday evening 22/04/2023 and the condition of the hospital is worst everywhere human waste and employees not taking care of patients there is
no proper response from doctors and today is Wednesday but there is no progress can you please have look into the issue asap
```
[/INST]Label: 1</s><s>[INST]### Text:
```
Good morning sir we are living in chennai ramapuram here nearby miot hospital ramapuram road mgr house road there is one wine shop and
more than 20 infected dogs biting and barking everyone in evening 7to10 time people's get troubled and afraid to come that side kindly please
solve this issue. Women's and childrens were there already we get troubling by drunken guys
```
[/INST]Label : 0</s><s>[INST]### Text:
```
{review}
```
[/INST]Label: """.strip()

    encoding = tokenizer(prompt, return_tensors="pt").to(device)
    # print(f"Token length = {len(encoding['input_ids'][0])}",end = ' Label = ')
    with torch.inference_mode():
        outputs = model.generate(
            **encoding,
            top_k = 1,
            max_new_tokens = 2,
            pad_token_id = 2,
            # stopping_criteria=StoppingCriteriaList([StopOnTokens()])
        )

    predict = tokenizer.decode(
        outputs[0][len(encoding['input_ids'][0]):],
        skip_special_tokens=True
    )
    prediction.append(predict.strip("' \n"))
    print(predict)

pre_result = []

for pre in prediction:
  if pre == '1':
    pre_result.append(1)
  else:
    pre_result.append(0)

conf_matrix = confusion_matrix(short_reviews['Complaint/Non Complaint'], pre_result)
accuracy = accuracy_score(short_reviews['Complaint/Non Complaint'], pre_result)
precision = precision_score(short_reviews['Complaint/Non Complaint'], pre_result)
recall = recall_score(short_reviews['Complaint/Non Complaint'], pre_result)
f1 = f1_score(short_reviews['Complaint/Non Complaint'], pre_result)

# Display the confusion matrix and performance metrics
print("Confusion Matrix:")
print(conf_matrix)
print("\nAccuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1 Score:", f1)

short_reviews['Binary Pred']= pre_result



"""# **Prediction Analysis**"""

short_reviews['Predictions'] = pre_result_f            # pre_result_f  for few shot, pre_result for zero shot

short_non_complaint = (short_reviews['Predictions'] == 0).sum()

print("Total Dataset: ", len(short_reviews))
print(f"Number of Complaints are {len(short_reviews) - short_non_complaint}")
print(f"Number of non complaints are {short_non_complaint}")

#segregating only predicted complaints from the dataset

aspect_df = short_reviews[short_reviews['Predictions'] == 1]

aspect_df

"""# **Multilabel Aspect class Zero Shot**"""

aspect_pred = []
i=0

for review in aspect_df['Full Complaint']:
  # %%time
  device = "cuda:0"

  prompt = f"""
        ###Instruction###
        You are a text classifier for healthcare domain, you are expert in classify the text.
        Classify the text given to you in one or more most relevant Aspect classes, but not more than 6 classes,
        your response must have most relevant Aspect classes in a list using comma as a delimiter,
        do not give any explanation or any note, only return the python list containing relevant Aspect classes.

              ### Aspect Classes ###
              1. 'Product'
              2. 'Negligence'
              3. 'Dispute'
              4. 'Service'
              5. 'Billing'
              6. 'Shortage'
              7. 'Accusation'
              8. 'Behaviour'
              9. 'Dirty'
              10. 'Online'
              11. 'Time'
              12.'Pharmacy'

        ###Find Aspect classes for below text###
        {short_reviews['Full Complaint'][152]}

        Your response:[
        """.strip()



  encoding = tokenizer(prompt, return_tensors="pt").to(device)
  with torch.inference_mode():
    outputs = model.generate(
        input_ids = encoding.input_ids,
        attention_mask = encoding.attention_mask,
        # generation_config = generation_config,
        num_return_sequences=1,  # Set this to 1

        stopping_criteria=StoppingCriteriaList([StopOnTokens()])

        )

  predict = tokenizer.decode(outputs[0], skip_special_tokens=True)
  # print(predict)
  response_index = predict.find("Your response:")
  response_label = predict[response_index + len("Your response:"):].strip()
  print(response_label)

short_reviews['Full Complaint'][152]

device = "cuda:0"

prompt = f"""
      ###Instruction###
      You are a text classifier for healthcare domain, you are expert in classify the text.
      Classify the text given to you in one or more most relevant Aspect classes, but not more than 6 classes,
      your response must have most relevant Aspect classes in a list using comma as a delimiter,
      do not give any explanation or any note, only return the python list containing relevant Aspect classes.

            ### Aspect Classes ###
            1. 'Billing'
            2. 'Negligence'
            3. 'Behaviour'
            4. 'Service'
            5. 'Time'
            6. 'Shortage'
            7. 'Accusation'
            8. 'Dispute'
            9. 'Dirty'
            10. 'Online'
            11. 'Pharmacy'
            12. 'Product'

      ###Find Aspect classes for below text###
      {short_reviews['Full Complaint'][152]}

      Your response:[
      """.strip()



encoding = tokenizer(prompt, return_tensors="pt").to(device)
with torch.inference_mode():
  outputs = model.generate(
      input_ids = encoding.input_ids,
      attention_mask = encoding.attention_mask,
      # generation_config = generation_config,
      num_return_sequences=1,  # Set this to 1

      stopping_criteria=StoppingCriteriaList([StopOnTokens()])

      )

predict = tokenizer.decode(outputs[0], skip_special_tokens=True)
# print(predict)
response_index = predict.find("Your response:")
response_label = predict[response_index + len("Your response:"):].strip()
print(response_label)



"""# **Multilabel Aspect class few Shot**"""

from transformers import StoppingCriteria, StoppingCriteriaList

class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        stop_ids = 2996
        if ']' in tokenizer.decode(input_ids[0][-1]):
          return True
        return False

generation_config = model.generation_config
generation_config.max_new_tokens = 100                          #Avg length of output generated by model
generation_config.temperature = 0.08                             #Smaller temp - fact; Larger temp - Creativity to model (Defrines randomness)
generation_config.top_p = 0.07                                    #top_p - Nuclueus Sampling, takes only (top_p) samples, large- Diverse, small - facts
generation_config.num_return_sequences = 1
generation_config.pad_token_id = tokenizer.eos_token_id
generation_config.eos_token_id = tokenizer.eos_token_id
generation_config.do_sample = True  # Adjust based on your preference for sampling

pred = []
i=0
from tqdm.notebook import tqdm
for review in tqdm(short_reviews['Full Complaint']):
    # %%time
    device = "cuda:0"

    prompt = f"""<<SYS>>Your task is to classify text.

Choose one or more labels among the following possibilities with the highest probability.
Only return the labels in python list, nothing more:

### Classes:
Service
Negligence
Behaviour
Cleanliness
Pharmacy
Unprofessionalism
Inefficiency
Unavailibility
Billing

<</SYS>>[INST]### Text:
```
This hopsital provides quality care because they have staff that is very passionate and professional and care for thier patients.
```
[/INST]Label : [Service, Unprofessionalism]</s><s>[INST]### Text:
```
Prescription is not good in this Hospital. Staff attitude is not good. Equipment is not good. Cleaning is average. Doctor wants
earn more money. Availability of blood is above average. Thank you.
```
[/INST]Label : [Behaviour, Cleanliness, Billing, Unprofessionalism]</s><s>[INST]### Text:
```
{review}
```
[/INST]Label: """.strip()

    encoding = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.inference_mode():
        outputs = model.generate(
        input_ids = encoding.input_ids,
        attention_mask = encoding.attention_mask,
        generation_config = generation_config,
        num_return_sequences=1,  # Set this to 1

        stopping_criteria=StoppingCriteriaList([StopOnTokens()])
    )

    predict = tokenizer.decode(outputs[0][len(encoding[0]):], skip_special_tokens=True)
    print(predict)
    # response_index = predict.find("Your response:")
    # response_label = predict[response_index + len("Your response:"):].strip()
    pred.append(predict)
    # i=i+1
    # #print(i)
    # print(r)

short_reviews['Multilabel pred']= pred
short_reviews.to_csv('mistral_instruct.csv', index=False)



"""# **Multilabel Results**"""

mapping = {'Service': 1, 'Negligence': 2, 'Behaviour': 3, 'Cleanliness': 4,
           'Pharmacy': 5, 'Unprofessionalism': 6, 'Inefficiency': 7,
           'Unavailibility': 8, 'Billing': 9}


reslt = []

for item in short_reviews['Multilabels']:
    lst = []
    for i in item:
        # Check if the key exists in the mapping dictionary
        if i in mapping:
            lst.append(mapping[i])
        else:
            # Handle the case where the key doesn't exist
            print(f"Key '{i}' not found in mapping dictionary")
    reslt.append(lst)

short_reviews['Multilabels Act'] = reslt

reslt = []

for item in short_reviews['Multilabel pred']:
    lst = []
    # Convert the string representation of the list to an actual list
    item_list = item.strip("[]").split(", ")
    for i in item_list:
        # Check if the key exists in the mapping dictionary
        if i.strip("'") in mapping:
            lst.append(mapping[i.strip("'")])
        else:
            # Handle the case where the key doesn't exist
            print(f"Key '{i.strip()}' not found in mapping dictionary")
    reslt.append(lst)


short_reviews['Multilabel pre'] = reslt

import ast

fnl = []

for lst in short_reviews['Multilabels Act']:
    #lst = ast.literal_eval(lst_str)            # Convert string representation of list to actual list
    intr = []
    for i in range(1, 10):                     # Changed range from 9 to 10, and starting index from 0 to 1
        if i in lst:
            intr.append(1)
        else:
            intr.append(0)
    fnl.append(intr)

short_reviews['1hot_act'] = fnl

fnl = []

for lst in short_reviews['Multilabel pre']:
    #lst = ast.literal_eval(lst_str)            # Convert string representation of list to actual list
    intr = []
    for i in range(1, 10):                     # Changed range from 9 to 10, and starting index from 0 to 1
        if i in lst:
            intr.append(1)
        else:
            intr.append(0)
    fnl.append(intr)

short_reviews['1hot_pred'] = fnl

short_reviews.head()

y_true = np.array(short_reviews['1hot_act'].tolist())
y_pred = np.array(short_reviews['1hot_pred'].tolist())

# Calculate multilabel confusion matrix
confusion_matrices = multilabel_confusion_matrix(y_true, y_pred)

# Display confusion matrices
for i, confusion_matrix in enumerate(confusion_matrices):
    print(f'Confusion matrix for label {i + 1}:')
    print(confusion_matrix)

report = classification_report(
    y_true,
    y_pred,
    output_dict=True,
    target_names=['Service', 'Negligence', 'Behaviour', 'Cleanliness', 'Pharmacy', 'Unprofessionalism', 'Inefficiency', 'Unavailability', 'Billing']
)

pprint.pprint(report)