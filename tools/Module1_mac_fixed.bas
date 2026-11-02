Attribute VB_Name = "Module1"
Sub ExportCustomConcatenationToFile()
    Dim fso As Object
    Dim exportPath As String
    Dim wbPath As String
    Dim fileName As String
    Dim customName As String
    Dim finalString As String

    Dim wsContext As Worksheet
    Dim wsAssets As Worksheet
    
    Dim lastRow As Long
    Dim i As Long
    Dim assets As String
    Dim inscene As String
    Dim firstItem As Boolean


    ' Assign worksheet objects
    Set wsContext = ThisWorkbook.Sheets("Context")
    Set wsAssets = ThisWorkbook.Sheets("Assets")

    ' Get workbook folder path
    wbPath = ThisWorkbook.Path
    If wbPath = "" Then
        MsgBox "Please save the workbook first to define a folder for export.", vbExclamation
        Exit Sub
    End If

    ' Determine filename from Context!B10 or fallback to workbook name
    customName = Trim(wsContext.Range("B10").Value)
    If customName <> "" Then
        fileName = customName
    Else
        fileName = Left(ThisWorkbook.Name, InStrRev(ThisWorkbook.Name, ".") - 1)
    End If
    
    ' Build the full export path
    exportPath = wbPath & Application.PathSeparator & fileName & ".json"

    
    lastRow = wsAssets.Cells(wsAssets.Rows.Count, "A").End(xlUp).Row
    
    ' Assets
    firstItem = True
    For i = 3 To lastRow
        If Trim(wsAssets.Cells(i, "A").Value) <> "" Then

            If Not firstItem Then
                assets = assets & ","
            End If
            assets = assets & wsAssets.Cells(i, "AX").Value
            firstItem = False
        End If
    Next i
    
    ' In scene
    firstItem = True
    For i = 3 To lastRow
        If Trim(wsAssets.Cells(i, "A").Value) <> "" Then
            If Trim(wsAssets.Cells(i, "B").Value) = 1 Then

                If Not firstItem Then
                    inscene = inscene & ","
                End If
                inscene = inscene & """" & wsAssets.Cells(i, "A").Value & """"
                firstItem = False
            End If
        End If
    Next i
    
    
    ' Build the final export string
    finalString = wsContext.Range("D1").Value & _
                  wsContext.Range("B4").Value & _
                  wsContext.Range("E1").Value & _
                  wsContext.Range("B5").Value & _
                  wsContext.Range("F1").Value & _
                  wsContext.Range("B6").Value & _
                  """}," & _
                  wsContext.Range("G1").Value & _
                  inscene & _
                  wsContext.Range("H1").Value & _
                  assets & _
                  "]}"
                  
    ' Create and write the output file
    'Dim txtFile As Object
    'Set fso = CreateObject("Scripting.FileSystemObject")
    'Set txtFile = fso.CreateTextFile(exportPath, True, True) ' overwrite=True, Unicode=True
    'txtFile.Write finalString
    'txtFile.Close
  
    Dim txtFile As Integer
    finalString = FormatJson(finalString)
    txtFile = FreeFile
    Open exportPath For Output As #txtFile
    Print #txtFile, finalString
    Close #txtFile

    

    'MsgBox "Export complete! File saved to: " & exportPath
End Sub



Sub ExportAnimationToFile()
    Dim fso As Object
    Dim exportPath As String
    Dim wbPath As String
    Dim fileName As String
    Dim customName As String
    Dim finalString As String

    Dim wsContext As Worksheet
    Dim wsAnim As Worksheet
    Dim wsSeq As Worksheet
    
    Dim lastRow As Long
    Dim i As Long
    Dim anims As String
    Dim sequences As String
    Dim firstItem As Boolean


    ' Assign worksheet objects
    Set wsContext = ThisWorkbook.Sheets("Context")
    Set wsAnim = ThisWorkbook.Sheets("Anim")
    Set wsSeq = ThisWorkbook.Sheets("Sequences")

    ' Get workbook folder path
    wbPath = ThisWorkbook.Path
    If wbPath = "" Then
        MsgBox "Please save the workbook first to define a folder for export.", vbExclamation
        Exit Sub
    End If

    ' Determine filename from Context!B10 or fallback to workbook name
    customName = Trim(wsContext.Range("B10").Value)
    If customName <> "" Then
        fileName = customName
    Else
        fileName = Left(ThisWorkbook.Name, InStrRev(ThisWorkbook.Name, ".") - 1)
    End If
    
    ' Build the full export path
    exportPath = wbPath & Application.PathSeparator & fileName & "_anim.json"

    
    lastRow = wsAnim.Cells(wsAnim.Rows.Count, "A").End(xlUp).Row
    
    ' Anim
    firstItem = True
    For i = 3 To lastRow
        If Trim(wsAnim.Cells(i, "A").Value) <> "" Then

            If Not firstItem Then
                anims = anims & ","
            End If
            anims = anims & wsAnim.Cells(i, "V").Value
            firstItem = False
        End If
    Next i
    
    ' Sequence
    firstItem = True
    For i = 3 To lastRow
        If Trim(wsSeq.Cells(i, "A").Value) <> "" Then

            If Not firstItem Then
                sequences = sequences & ","
            End If
            sequences = sequences & wsSeq.Cells(i, "O").Value
            firstItem = False
        End If
    Next i
    
   
    
    ' Build the final export string
    finalString = wsContext.Range("D2").Value & _
                  wsContext.Range("B4").Value & _
                  wsContext.Range("E2").Value & _
                  wsContext.Range("B5").Value & _
                  wsContext.Range("F2").Value & _
                  wsContext.Range("B7").Value & _
                  wsContext.Range("G2").Value & _
                  anims & _
                  wsContext.Range("H2").Value & _
                  sequences & _
                  wsContext.Range("I2").Value
                  
                  
    ' Create and write the output file
    'Dim txtFile As Object
    'Set fso = CreateObject("Scripting.FileSystemObject")
    'Set txtFile = fso.CreateTextFile(exportPath, True, True) ' overwrite=True, Unicode=True
    'txtFile.Write finalString
    'txtFile.Close
  
    Dim txtFile As Integer
    finalString = FormatJson(finalString)
    txtFile = FreeFile
    Open exportPath For Output As #txtFile
    Print #txtFile, finalString
    Close #txtFile

    

    'MsgBox "Export complete! File saved to: " & exportPath
End Sub



Function FormatJson(json As String) As String

    Dim i As Long
    Dim j As Long
    Dim indent As Long
    Dim result As String
    Dim ch As String
    Dim inString As Boolean
    
    For i = 1 To Len(json)

        ch = Mid$(json, i, 1)

        If ch = """" Then
        
            ' Ignore escaped quotes
            If i = 1 Or Mid$(json, i - 1, 1) <> "\" Then
                inString = Not inString
            End If
            
            result = result & ch

        ElseIf Not inString Then

            Select Case ch

            Case "["
            
                j = FindMatchingBracket(json, i)

                If j > 0 Then
                    If IsNumericArray(Mid$(json, i, j - i + 1)) Then
                        
                        ' Keep numeric array on one line
                        result = result & FormatNumericArray(Mid$(json, i, j - i + 1))
                        i = j
                        
                    Else
                        
                        result = result & "[" & vbCrLf
                        indent = indent + 1
                        result = result & Space(indent * 2)
                        
                    End If
                Else
                
                    result = result & ch
                    
                End If

            Case "{"
            
                result = result & "{" & vbCrLf
                indent = indent + 1
                result = result & Space(indent * 2)

            Case "}", "]"
            
                indent = indent - 1
                result = result & vbCrLf & Space(indent * 2) & ch

            Case ","
            
                result = result & "," & vbCrLf & Space(indent * 2)

            Case ":"
            
                result = result & ": "

            Case Else
            
                result = result & ch

            End Select

        Else
        
            result = result & ch

        End If

    Next i

    FormatJson = result

End Function

Function FindMatchingBracket(ByVal json As String, ByVal startPos As Long) As Long

    Dim level As Long
    Dim i As Long
    Dim ch As String
    Dim inString As Boolean

    For i = startPos To Len(json)

        ch = Mid$(json, i, 1)

        If ch = """" Then
            If i = 1 Or Mid$(json, i - 1, 1) <> "\" Then
                inString = Not inString
            End If
        ElseIf Not inString Then
            If ch = "[" Then
                level = level + 1
            ElseIf ch = "]" Then
                level = level - 1
                If level = 0 Then
                    FindMatchingBracket = i
                    Exit Function
                End If
            End If
        End If

    Next i

End Function

Function IsNumericArray(ByVal s As String) As Boolean

    Dim inner As String
    Dim i As Long
    Dim ch As String

    inner = Trim$(s)

    If Left$(inner, 1) <> "[" Or Right$(inner, 1) <> "]" Then Exit Function

    inner = Mid$(inner, 2, Len(inner) - 2)

    For i = 1 To Len(inner)

        ch = Mid$(inner, i, 1)

        Select Case ch
            Case "0" To "9", ",", ".", "-", "+", " ", "E", "e"
                ' allowed
            Case Else
                Exit Function
        End Select

    Next i

    IsNumericArray = True

End Function


Function FormatNumericArray(ByVal s As String) As String

    Do While InStr(s, ", ") > 0
        s = Replace(s, ", ", ",")
    Loop

    FormatNumericArray = Replace(s, ",", ", ")

End Function
