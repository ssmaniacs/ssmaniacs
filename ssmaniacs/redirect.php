<?php
$url = $_SERVER["QUERY_STRING"];
$header = array(
  "User-Agent: " . $_SERVER["HTTP_USER_AGENT"],
  "Content-Type: " . $_SERVER["CONTENT_TYPE"]
);

$curl = curl_init();
curl_setopt($curl, CURLOPT_URL, $url);
curl_setopt($curl, CURLOPT_HTTPHEADER, $header);
curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);

if ($_SERVER["REQUEST_METHOD"] == "POST") {
  $data = file_get_contents("php://input");
  curl_setopt($curl, CURLOPT_POST, 1);
  curl_setopt($curl, CURLOPT_POSTFIELDS, $data);
}

$response = curl_exec($curl);
curl_close($curl);

echo $response;
?>
