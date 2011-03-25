<?php

require_once   ('scraperwiki/datastore.php') ;
require_once   ('scraperwiki/metadata.php' ) ;
require_once   ('scraperwiki/stacktrace.php' ) ;
require_once   ('scraperwiki/apiwrapper.php' ) ;

class scraperwiki
{
   private static $m_cacheFor = 0 ;

   static function sw_allowCache ($cacheFor)
   {
      self::$m_cacheFor = $cacheFor ;
   }

   static function sw_dumpMessage ($dict)
   {
      global $logfd ;
      fwrite ($logfd, json_encode ($dict) . "\n") ;
   }

   static function sw_logScrapedURL ($url, $length)
   {
       scraperwiki::sw_dumpMessage
           /* seexception(errmap):
        mess = errmap["error"]
        for k, v in errmap.items():
        if k != "error" {
            mess = "%s; %s:%s" % (mess, k, v)

        if re.match('sqlite3.Error: no such table:', mess):
        return NoSuchTableSqliteError(mess)
    return SqliteError(mess)


def save_sqlite(unique_keys, data, table_name="swdata", verbose=2):
    ds = DataStore(None)
    result = ds.save_sqlite(unique_keys, data, table_name)
    if "error" in result:
        raise databaseexception(result)
            */

         (  array
            (  'message_type' => 'sources',
               'url'          => $url,
               'content'      => sprintf ("%d bytes from %s", $length, $url)
         )  )  ;
   }

   static function httpresponseheader ($headerkey, $headervalue)
   {
       scraperwiki::sw_dumpMessage
         (  array
            (  'message_type' => 'httpresponseheader',
               'headerkey'    => $headerkey,
               'headervalue'  => $headervalue
         )  )  ;
   }

   static function save ($unique_keys, $data, $date = null, $latlng = null)
   {
      $ds      = SW_DataStoreClass::create () ;
   
      $result  = $ds->save ($unique_keys, $data, $date, $latlng) ;
      if (! $result[0])
         throw new Exception ($result[1]) ;

      scraperwiki::sw_dumpMessage (array('message_type' => 'data', 'content' => $data)) ;
   }

   static function sqlitecommand($command, $val1 = null, $val2 = null)
   {
      $ds = SW_DataStoreClass::create();
      $result = $ds->request(array('sqlitecommand', $command, $val1, $val2));
      if (property_exists($result, 'error'))
         throw new Exception ($result->error) ;
      scraperwiki::sw_dumpMessage (array('message_type'=>'sqlitecall', 'command'=>$command, 'val1'=>$val1, 'val2'=>$val2));
      return $result; 
   }

   static function save_sqlite($unique_keys, $data, $table_name="swdata", $verbose=2)
   {
      $ds = SW_DataStoreClass::create () ;
      $result = $ds->request(array('save_sqlite', $unique_keys, $data, $table_name)); 
      if (property_exists($result, 'error'))
         throw new Exception ($result->error) ;
      scraperwiki::sw_dumpMessage (array('message_type'=>'data', 'content'=>$data)) ;
   }

   static function gb_postcode_to_latlng ($postcode)
   {
      if (is_null($postcode))
         return null ;

      $ds      = SW_DataStoreClass::create () ;

      $result  = $ds->postcodeToLatLng ($postcode) ;
      if (! $result[0])
      {
         scraperwiki::sw_dumpMessage
            (  array
                  (  'message_type' => 'console',
                     'content'      => 'Warning: ' + sprintf('%s: %s', $result[1], $postcode)
                  )
            )  ;
        return null  ;
      }

      return $result[1] ;
   }

   static function scrape ($url)
   {
      $curl = curl_init ($url ) ;
      curl_setopt ($curl, CURLOPT_RETURNTRANSFER, true) ;
      $res  = curl_exec ($curl) ;
      curl_close ($curl) ;
      return   $res;
   }

   static function cache ($enable = true)
   {
      file_get_html
         (  sprintf
            (  "http://127.0.0.1:9001/Option?runid=%s&webcache=%s",
               getenv('RUNID'),
               $enable ? self::$m_cacheFor : 0
         )  )  ;
   }

   static function get_metadata($metadata_name, $default = null)
   {
      return SW_MetadataClient::create()->get($metadata_name);
   }

   static function save_metadata($metadata_name, $value)
   {
      print "Saving " . $metadata_name . ": " . $value . "\n";
      return SW_MetadataClient::create()->save($metadata_name, $value);
   }


    static function getKeys($name) {
        return SW_APIWrapperClass::getKeys($name); 
    }
    static function getData($name, $limit= -1, $offset= 0) {
        return SW_APIWrapperClass::getData($name, $limit, $offset); 
    }

    static function getDataByDate($name, $start_date, $end_date, $limit= -1, $offset= 0) {
        return SW_APIWrapperClass::getDataByDate($name, $start_date, $end_date, $limit, $offset); 
    }
    
    static function getDataByLocation($name, $lat, $lng, $limit= -1, $offset= 0) { 
        return SW_APIWrapperClass::getDataByLocation($name, $lat, $lng, $limit, $offset); 
    }
        
    static function search($name, $filterdict, $limit= -1, $offset= 0) {
        return SW_APIWrapperClass::search($name, $filterdict, $limit, $offset);
    }
}

?>
