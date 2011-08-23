<?php

function exceptionHandler($exception, $script) 
{
    $stackdump = array(); 
    $scriptlines = explode("\n", file_get_contents($script)); 
    $trace = $exception->getTrace(); 
    for ($i = count($trace) - 2; $i >= 0; $i--)
    {
        $stackPoint = $trace[$i]; 
        $linenumber = $stackPoint["line"]; 
        $stackentry = array("linenumber" => $linenumber, "duplicates" => 1); 
        $stackentry["file"] = ($stackPoint["file"] == $script ? "<string>" : $stackPoint["file"]); 

        if (($linenumber >= 0) && ($linenumber < count($scriptlines)))
            $stackentry["linetext"] = $scriptlines[$linenumber]; 

        if (array_key_exists("args", $stackPoint) and count($stackPoint["args"]) != 0)
        {
            $args = array(); 
            foreach ($stackPoint["args"] as $arg => $val)
                $args[] = $arg."=>".$val; 
            $stackentry["furtherlinetext"] = " param values: (".implode(", ", $args).")"; 
        }
        $stackdump[] = $stackentry; 
    }
    
    $linenumber = $exception->getLine(); 
    $finalentry = array("linenumber" => $linenumber, "duplicates" => 1); 
    $finalentry["file"] = ($exception->getFile() == $script ? "<string>" : $exception->getFile()); 
    if (($linenumber >= 0) && ($linenumber < count($scriptlines)))
        $finalentry["linetext"] = $scriptlines[$linenumber]; 
    $finalentry["furtherlinetext"] = $exception->getMessage().count($scriptlines); 
    $stackdump[] = $finalentry; 
    
    return array('message_type' => 'exception', 'exceptiondescription' => $exception->getMessage(), "stackdump" => $stackdump); 
}


function errorParser($errno, $errstr, $errfile, $errline, $script)
{
    $codes = Array(
        1 => "E_ERROR",
        2 => "E_WARNING",
        4 => "E_PARSE",
        8 => "E_NOTICE",
        16 => "E_CORE_ERROR",
        32 => "E_CORE_WARNING",
        64 => "E_COMPILE_ERROR",
        128 => "E_COMPILE_WARNING",
        256 => "E_USER_ERROR",
        512 => "E_USER_WARNING",
        1024 => "E_USER_NOTICE",
        2048 => "E_STRICT",
        4096 => "E_RECOVERABLE_ERROR",
        8192 => "E_DEPRECATED",
        16384 => "E_USER_DEPRECATED",
    );
        // this function could use debug_backtrace() to obtain the whole stack for this error
    $stackdump = array(); 
    $scriptlines = explode("\n", file_get_contents($script)); 
    $linenumber = $errline; 
    $errorentry = array("linenumber" => $linenumber, "duplicates" => 1); 
    $errorentry["file"] = ($errfile == $script ? "<string>" : $errfile); 
    if (($linenumber >= 0) && ($linenumber < count($scriptlines)))
        $errorentry["linetext"] = $scriptlines[$linenumber]; 
    $errcode = $codes[$errno]; 

    $stackdump[] = $errorentry; 
    return array('message_type' => 'exception', 'exceptiondescription' => $errcode."  ".$errstr, "stackdump" => $stackdump); 
}


?>