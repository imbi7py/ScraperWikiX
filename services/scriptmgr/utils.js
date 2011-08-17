/******************************************************************************
* utils.js
*
* Utility functions for working with the processes locally
******************************************************************************/
var streamLogger = require('streamlogger');
var logger;

/******************************************************************************
* Set up logging to the specific file with the level where level = 
* debug: 0, info: 1, warn: 2, fatal: 3  
******************************************************************************/
exports.setup_logging = function( logfile, level ) {
	logger = new streamLogger.StreamLogger( logfile );	
	logger.level = level;
	
	process.on('SIGHUP', function () {
  		logger.reopen();
	});
	
	exports.log = logger;
};



var exts = {
	'python' : 'py', 
	'ruby'   : 'rb', 	
	'php'   : 'php', 		
	'javascript' : 'js',
}

/******************************************************************************
* Silly look up to get the extension for the language we are executing
******************************************************************************/
exports.extension_for_language = function( lang ) {
	return exts[lang];
};

/******************************************************************************
* Works out what environment variables we want to pass to the script
******************************************************************************/
exports.env_for_language = function( lang, extra_path ) {
	if ( lang == 'python' ) {
		return {PYTHONPATH: extra_path, PYTHONUNBUFFERED: 'true'};
	} else if ( lang == 'ruby') {
		return { RUBYLIB: extra_path };		
	} else if ( lang == 'php') {
		return { PHPPATH: extra_path};		
	} else if ( lang == 'js' ) {
		return { NODE_PATH: process.env.NODE_PATH + ":" + extra_path };
	}
	
};

				