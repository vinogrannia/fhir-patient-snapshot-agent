Class FHIR.Snapshot.EmbeddedPythonDemo Extends %RegisteredObject
{

ClassMethod NormalizeObservationValue(value As %String) As %String [ Language = python ]
{
import re

match = re.search(r"-?\d+(?:\.\d+)?", value or "")
return match.group(0) if match else ""
}

ClassMethod Demo() As %String
{
    Quit ..NormalizeObservationValue("Body Mass Index 30.35 kg/m2")
}

}
