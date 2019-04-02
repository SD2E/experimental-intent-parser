package com.bbn.sd2;

import java.io.FileOutputStream;

import com.google.api.services.docs.v1.model.Document;

class GoogleDocsTest {
    public static void main(String[] args) {
    	try {
    		GoogleDocsAccessor docsAccessor = new GoogleDocsAccessor();
	       	Document doc = docsAccessor.getDocument("1DLvkYbmnBsgeEwHyoms8l1RcCvvVFNl5dZWEIUKjaNM");
	       	System.out.println(doc.getTitle());
	       	FileOutputStream os = new FileOutputStream("doc.json");
	       	os.write(doc.toPrettyString().getBytes());
	       	os.close();
    	} catch( Exception e) {
    		e.printStackTrace();
    	}
    }
}
