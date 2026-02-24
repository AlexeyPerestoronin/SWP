Dim swApp As SldWorks.SldWorks
Dim swModel As ModelDoc2
Dim swPart As PartDoc
Dim i As Integer
Dim errors As Long
Dim warnings As Long
Dim saveFilePath As String
Dim status As Boolean

' Function to create directory
Function CreateDirectory(dirPath As String) As String
    On Error Resume Next
    MkDir dirPath
    On Error GoTo 0

    CreateDirectory = dirPath
End Function

Sub main()
     ' Initialize SOLIDWORKS
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    Set swPart = swModel

    ' Check that a document is open
    If swModel Is Nothing Then
        MsgBox "Open a document with multiple bodies", vbExclamation
        Exit Sub
    End If

    ' Check that a part is open
    If swModel Is Nothing Or swModel.GetType <> swDocPART Then
        MsgBox "This macro works only with parts", vbExclamation
        Exit Sub
    End If

    ' Check that document is saved on file-system
    Dim swPartFilePath As String
    swPartFilePath = swModel.GetPathName
    If swPartFilePath = "" Then
        MsgBox "Please save the document first", vbExclamation
        On Error GoTo 0
    End If

    ' Get all solid bodies
    Dim solidBodies As Variant
    solidBodies = swPart.GetBodies2(swSolidBodyAggregate, False)

    ' Check if solid bodies are present in the model
    If IsEmpty(solidBodies) Then
        MsgBox "No solid bodies found", vbExclamation
        Exit Sub
    End If

    Dim stepExportPath As String
    stepExportPath = CreateDirectory(Left(swPartFilePath, InStrRev(swPartFilePath, "\")) & "STEP_Export")

    For i = 0 To UBound(solidBodies)
        Dim swBody As Body2
        Set swBody = solidBodies(i)

        Dim swBodyName As String
        swBodyName = swBody.Name

        Dim swBodyMaterialName As String
        swBodyMaterialName = swBody.GetMaterialPropertyName("", "")

        Dim swBodySaveFolder As String
        swBodySaveFolder = CreateDirectory(stepExportPath & "\" & swBodyMaterialName)

        ' Doesn't save bodies with [NotFS] prefix in name
        If InStr(1, swBodyName, "[NotFS]", vbTextCompare) > 0 Then
            Debug.Print "Skipping body: " & swBodyName
        Else
            ' Clear selection and select current body
            swModel.ClearSelection2 True
            swBody.Select2 False, Nothing

            errors = 0
            warnings = 0
            saveFilePath = swBodySaveFolder  & "\" & swBodyName  & ".step"
            status = swModel.Extension.SaveAs(saveFilePath, 0, 1, Nothing, errors, warnings)
            If errors = 0 Then
                Debug.Print "Saved: " & saveFilePath
            Else
                Debug.Print "Error saving body " & (i + 1)
            End If
        End If
    Next i
End Sub
