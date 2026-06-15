Class FHIR.Snapshot.EmbeddedVectorSearch Extends %RegisteredObject
{

ClassMethod Vectorize(text As %String) As %String [ Language = python ]
{
import json
import re
from collections import Counter

tokens = [
    token.lower()
    for token in re.findall(r"[A-Za-z0-9]+", text or "")
    if len(token) > 1
]
return json.dumps(dict(Counter(tokens)), sort_keys=True)
}

ClassMethod CosineSimilarity(leftVectorJson As %String, rightVectorJson As %String) As %String [ Language = python ]
{
import json
import math

left = json.loads(leftVectorJson or "{}")
right = json.loads(rightVectorJson or "{}")
shared = set(left) & set(right)
if not shared:
    return "0"

dot_product = sum(left[token] * right[token] for token in shared)
left_norm = math.sqrt(sum(value * value for value in left.values()))
right_norm = math.sqrt(sum(value * value for value in right.values()))
if left_norm == 0 or right_norm == 0:
    return "0"

return str(dot_product / (left_norm * right_norm))
}

ClassMethod Demo() As %String
{
    Set queryVector = ..Vectorize("medications allergies labs")
    Set medicationVector = ..Vectorize("MedicationRequest Acetaminophen stopped Naproxen stopped")
    Quit ..CosineSimilarity(queryVector, medicationVector)
}

}
