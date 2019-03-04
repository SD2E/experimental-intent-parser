package com.bbn.sd2;

import com.google.api.services.docs.v1.model.Document;

class GoogleDocsTest {
    public static void main(String[] args) {
    	try {
    		GoogleDocsAccessor docsAccessor = new GoogleDocsAccessor();
	       	Document doc = docsAccessor.getDocument("1E10P6bH13naJp2eB5_epEgqUklCU6RHmzmLsyfNUPOw");
	       	System.out.println(doc.getTitle());
    	} catch( Exception e) {
    		
    	}
    }
}
