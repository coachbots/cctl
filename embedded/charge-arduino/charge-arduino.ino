void setup() {
  pinMode(A1, OUTPUT);
  pinMode(A3, OUTPUT);
  pinMode(A5, OUTPUT);
  digitalWrite(A1,HIGH);
  digitalWrite(A3,HIGH);
  digitalWrite(A5,HIGH);
  Serial.begin(115200);
}

void loop() {
  if (Serial.available() > 0) {
    // read the incoming byte:
    char incomingByte = Serial.read();

    if(incomingByte == 'A')
    {
      digitalWrite(A1,HIGH);
      digitalWrite(A3,HIGH);
      digitalWrite(A5,HIGH);
    }
    if(incomingByte == 'D')
    {
      digitalWrite(A1,LOW);
      digitalWrite(A3,LOW);
      digitalWrite(A5,LOW);
    }
  }
}
