/*
 * Copyright (C) 2009 Google Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 */

package org.odk.validate;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.OutputStream;
import java.io.PrintStream;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.javarosa.core.model.FormDef;
import org.javarosa.xform.parse.XFormParseException;
import org.javarosa.xform.util.XFormUtils;
import org.w3c.dom.Document;

/**
 * This is a skimmed down, headless version of ODK validate which 
 * "uses the javarosa-core library to process a form and show errors, if any."
 *
 * The code was cloned with the command:
 *    hg clone https://validate.opendatakit.googlecode.com/hg/ opendatakit-validate
 * and packaged with "ant package"
 * 
 * @author Adam Lerer (adam.lerer@gmail.com)
 * @author Yaw Anokwa (yanokwa@gmail.com)
 */

public class FormValidator {
    public static void main(String[] args) {
        String path = args[0];
        String error;
        FileInputStream fis = null;
        
        try {
            fis = new FileInputStream(new File(path));
        } catch(FileNotFoundException e) {
            System.err.println("\nError: File not found");
            return;
        }
        
        //validate well formed xml
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        DocumentBuilder builder = null;
        try {
            builder = factory.newDocumentBuilder();
            Document document = builder.parse(new File(path));
        } catch (Exception e) {
            System.err.println("\nResult: Invalid XML");
            return;
        }
        
        //validate if the xform can be parsed
        try {
            FormDef fd = XFormUtils.getFormFromInputStream(fis);
            if (fd == null) {
                System.err.println("\nResult: Broken - FormDef Null");
                return;
            }
            System.err.println("\nResult: Valid");
        } catch (XFormParseException e) {
            if (e.getMessage() == null) {
                e.printStackTrace();
            } else {
                System.err.println(e.getMessage());
            }
            System.err.println("\nResult: Invalid");
        } catch (Exception e) {
            if (e.getMessage() != null) {
                System.err.println(e.getMessage());
            }
            e.printStackTrace();
            System.err.println("\nResult: Broken");
        }
    }
}
