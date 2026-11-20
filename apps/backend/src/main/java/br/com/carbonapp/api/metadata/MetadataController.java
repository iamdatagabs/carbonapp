package br.com.carbonapp.api.metadata;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
@RestController
@RequestMapping("/api/v1/metadata")
public class MetadataController {
 private static final List<DepthMetadata> DEPTHS=List.of(
 new DepthMetadata("A",0,10,10),new DepthMetadata("B",10,20,10),new DepthMetadata("C",20,40,20),
 new DepthMetadata("D",40,60,20),new DepthMetadata("E",60,80,20),new DepthMetadata("F",80,100,20),
 new DepthMetadata("G",100,130,30),new DepthMetadata("H",130,160,30),new DepthMetadata("I",160,200,40));
 @GetMapping("/depths") public List<DepthMetadata> depths(){return DEPTHS;}
}
