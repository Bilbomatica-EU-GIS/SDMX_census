<?php 
$returnFile = false;

echo ("returnFile: $returnFile"); 

	$q= $_GET['q']; 
	$datasetId = $_GET['spatial_dataset_identifier_code']; 
	// if (!$datasetId) { 
		// if (!$q) {
			// header("Location: ATOM_download_service.xml"); 
			// exit; 
		// } 
		// $datasetId = $q; 
	// } 
	$namespace= $_GET['spatial_dataset_identifier_namespace']; 
	
	$language= $_GET['language'];
	$country= $_GET['country'];
	
	if ($country) { 
		$returnFile= true;
	}
	
	if (!$language || $language == "*"){ 
		$language = "en"; 
	} 
	
	if ($language != 'en'){
		die( "Only en is supported" ); 
	} 
	
	if ($namespace == "PD") {
		if ($returnFile){
			
			$ch = curl_init('http://localhost:8080/ATOM/PD/Data/'.$country.'_PD_3035_GML.zip');
			curl_setopt($ch, CURLOPT_NOBODY, true);
			curl_exec($ch);
			$retcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
			// $retcode >= 400 -> not found, $retcode = 200, found.
			curl_close($ch);
			
			if ($retcode == 200) {
				header('Location: http://localhost:8080/ATOM/PD/Data/'.$country.'_PD_3035_GML.zip');
			} else {
				header('Location: http://localhost:8080/ATOM/notFound.html');
			}
			
		} else {
			header('Location: http://localhost:8080/ATOM/PD/PD.atom');
		} 
		exit; 
	} elseif ($namespace == "SU") {
		 if ($returnFile){
			$ch = curl_init('http://localhost:8080/ATOM/SU/Data/'.$country.'_SU_3035_GML.zip');
			curl_setopt($ch, CURLOPT_NOBODY, true);
			curl_exec($ch);
			$retcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
			// $retcode >= 400 -> not found, $retcode = 200, found.
			curl_close($ch);
			
			if ($retcode == 200) {
				header('Location: http://localhost:8080/ATOM/SU/Data/'.$country.'_SU_3035_GML.zip');
			} else {
				header('Location: http://localhost:8080/ATOM/notFound.html');
			}
			
		} else {
			header('Location: http://localhost:8080/ATOM/SU/SU.atom');
		}
		exit;
	}

	//echo 'Not found';
	header('Location: http://localhost:8080/ATOM/notFound.html');
?>