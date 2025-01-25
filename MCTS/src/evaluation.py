import re
import string

def normalize_answer(s):
    def remove_articles(text):
        return re.sub(r"\b(a|an|the|usd)\b", " ", text)
    
    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def to_float(s):
    return s.replace("USD", '').replace("$", "").replace(",", "")


def EM(answer, predict) -> bool:
    answer, predict = str(answer).strip(), str(predict).strip()
    answer_float = to_float(answer)
    predict_float = to_float(predict)
    try:
        answer_float = float(answer_float)
        predict_float = float(predict_float)

        if answer_float == predict_float:
            return True
      
    except:
        pass

    answer_str = normalize_answer(str(answer))
    predict_str = normalize_answer(str(predict))

    if answer_str == predict_str:
        return True
    else:
        return False



if __name__=="__main__":
  answer_pari = [("1699 ", "1,699.000 USD")]

  for answer, predict in answer_pari:
    print(EM(answer, predict))