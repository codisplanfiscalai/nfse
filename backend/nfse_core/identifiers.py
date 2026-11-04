from __future__ import annotations
import re


def valid_tax_id(raw: str) -> bool:
    value=re.sub(r'\D','',raw or '')
    if len(value)==11:
        if len(set(value))==1:return False
        digits=[int(x) for x in value]
        for length in (9,10):
            summed=sum(digits[j]*(length+1-j) for j in range(length))
            check=(summed*10)%11
            if check==10:check=0
            if digits[length]!=check:return False
        return True
    if len(value)==14:
        if len(set(value))==1:return False
        digits=[int(x) for x in value]
        for length,weight in ((12,[5,4,3,2,9,8,7,6,5,4,3,2]),(13,[6,5,4,3,2,9,8,7,6,5,4,3,2])):
            remainder=sum(x*w for x,w in zip(digits[:length],weight))%11
            check=0 if remainder<2 else 11-remainder
            if digits[length]!=check:return False
        return True
    return False
