package br.com.carbonapp.mobile
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
 override fun onCreate(savedInstanceState: Bundle?) {
  super.onCreate(savedInstanceState)
  setContent { MaterialTheme { Surface(Modifier.fillMaxSize()) { FieldCaptureScreen() } } }
 }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FieldCaptureScreen() {
 var project by remember { mutableStateOf("DEMO") }
 var point by remember { mutableStateOf("") }
 var depth by remember { mutableStateOf("A") }
 var notes by remember { mutableStateOf("") }
 var saved by remember { mutableStateOf(false) }
 var expanded by remember { mutableStateOf(false) }
 val depths=listOf("A · 0–10 cm","B · 10–20 cm","C · 20–40 cm","D · 40–60 cm","E · 60–80 cm","F · 80–100 cm","G · 100–130 cm","H · 130–160 cm","I · 160–200 cm")
 Column(Modifier.fillMaxSize().padding(24.dp),verticalArrangement=Arrangement.spacedBy(14.dp)) {
  Text("CarbonApp",style=MaterialTheme.typography.headlineMedium)
  Text("Registro de campo · MVP 0",style=MaterialTheme.typography.titleMedium)
  OutlinedTextField(project,{project=it;saved=false},label={Text("Projeto")},modifier=Modifier.fillMaxWidth())
  OutlinedTextField(point,{point=it;saved=false},label={Text("Ponto de amostragem")},modifier=Modifier.fillMaxWidth())
  ExposedDropdownMenuBox(expanded=expanded,onExpandedChange={expanded=!expanded}) {
   OutlinedTextField(depth,{},readOnly=true,label={Text("Camada de profundidade")},modifier=Modifier.menuAnchor().fillMaxWidth())
   ExposedDropdownMenu(expanded=expanded,onDismissRequest={expanded=false}) {
    depths.forEachIndexed { index,label -> DropdownMenuItem(text={Text(label)},onClick={depth=('A'.code+index).toChar().toString();expanded=false;saved=false}) }
   }
  }
  OutlinedTextField(notes,{notes=it;saved=false},label={Text("Observações")},minLines=3,modifier=Modifier.fillMaxWidth())
  Button(onClick={saved=project.isNotBlank()&&point.isNotBlank()},enabled=project.isNotBlank()&&point.isNotBlank()) { Text("Salvar rascunho local") }
  if(saved) Card(Modifier.fillMaxWidth()) {
   Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(4.dp)) {
    Text("Rascunho validado nesta sessão",color=MaterialTheme.colorScheme.primary)
    Text("Projeto: $project · Ponto: $point · Camada: $depth")
    Text("Ainda não sincronizado com o servidor.")
   }
  }
  Text("Protótipo de interface: persistência offline, autenticação e sincronização serão implementadas nas próximas etapas.",style=MaterialTheme.typography.bodySmall)
 }
}
