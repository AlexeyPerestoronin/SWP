Dim swApp As SldWorks.SldWorks
Dim swModel As ModelDoc2
Dim swPart As PartDoc
Dim i As Integer
Dim errors As Long
Dim warnings As Long

Sub main()
     ' Инициализация SOLIDWORKS
    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    Set swPart = swModel
    
    ' Настройка параметров экспорта в STEP (по умолчанию обычно AP214)
    ' swApp.SetUserPreferenceIntegerValue swUserPreferenceIntegerValue_e.swStepAP, 214

    ' Проверка, что открыт документ
    If swModel Is Nothing Then
        MsgBox "Откройте документ с многотельными телами", vbExclamation
        Exit Sub
    End If

    ' Проверка, что открыта деталь
    If swModel Is Nothing Or swModel.GetType <> swDocPART Then
        MsgBox "Этот макрос работает только с деталями (Part)", vbExclamation
        Exit Sub
    End If

    ' Получение всех твердых тел
    Dim solidBodies As Variant
    solidBodies = swPart.GetBodies2(swSolidBodyAggregate, False)

    ' Проверка, твёрдые тела присутствуют в модели
    If IsEmpty(solidBodies) Then
        MsgBox "Не найдено ни одного твёрдого тела", vbExclamation
        Exit Sub
    End If

    ' Получаем базовое имя файла детали без расширения
    Dim origPath As String
    origPath = swModel.GetPathName
    If origPath = "" Then
        MsgBox "Сначала сохраните документ", vbExclamation
        Exit Sub
    End If

    ' Создаем папку для STEP-файлов рядом с исходным файлом
    Dim exportPath As String
    exportPath = Left(origPath, InStrRev(origPath, "\")) & "STEP_Export\"
    On Error Resume Next
    MkDir exportPath
    On Error GoTo 0

    For i = 0 To UBound(solidBodies)
        Dim swBody As Body2
        Set swBody = solidBodies(i)

        ' Очищаем выделение и выбираем текущее тело
        swModel.ClearSelection2 True
        Dim status As Boolean
        swBody.Select2 False, Nothing

        ' Формируем имя файла: ИсходноеИмя_ТелоN.step
        Dim filePath As String
        filePath = exportPath & swBody.Name & ".step"

        
        errors = 0
        warnings = 0
        ' swSaveAsCurrentVersion = 0
        ' swSaveAsOptions_Silent = 1 (сохранение без лишних окон)
        status = swModel.Extension.SaveAs(filePath, 0, 1, Nothing, errors, warnings)
        
        If errors = 0 Then
            Debug.Print "Сохранено: " & filePath
        Else
            Debug.Print "Ошибка при сохранении тела " & (i + 1)
        End If
    Next i
End Sub
