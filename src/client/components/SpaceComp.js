import React from "react";
import { useRef } from 'react';
import PropTypes from 'prop-types'
import * as Constants from '../constants/Space'

//ui
import '../css/Form.css';

import { Button, Modal, Row, Col, Card, ButtonToolbar, CardColumns, Spinner, Image, Badge, Alert } from 'react-bootstrap';
import { Formik, Field, Form, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { IconButton } from '@material-ui/core';
import LabelIcon from '@material-ui/icons/Label';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import CardGiftcardIcon from '@material-ui/icons/CardGiftcard';
import VisibilityIcon from '@material-ui/icons/Visibility';

const validateFormSchema = Yup.object().shape({
  name: Yup.string()
    .required("Name is required")
    .min(3, 'Name must be at least 3 characters')
    .trim(),
  colorCode: Yup.string()
    .required("Color is required")
    .min(1, 'Please select Color'),
  location: Yup.string()
    .required('Location is required')
    .min(1, 'Please select location'),
  tags: Yup.string().nullable()
    .min(3, 'Tags must be at least 3 characters')
    .trim(),
  sizeUnit: Yup.string().nullable()
    .when(['sizeWidth', 'sizeHeight', 'sizeDepth'], {
      is: (sizeWidth, sizeHeight, sizeDepth) => sizeWidth > 0 || sizeHeight > 0 || sizeDepth > 0,
      then: Yup.string().required('Unit is required')
    }),
  sizeWidth: Yup.number().nullable()
    .min(0, 'Please enter valid Width'),
  sizeHeight: Yup.number().nullable()
    .min(0, 'Please enter valid Height'),
  sizeDepth: Yup.number().nullable()
    .min(0, 'Please enter valid Depth'),
})

//generate space list content
const genSpaceData = (space, key, handleEdit, handleSelect, handleDelete) => {
  let tagsArr = {};
  if (space.tags != null && space.tags.length > 0) {
    tagsArr = space.tags.split(',');
  }

  return <Card key={key} bg={space.colorCode.toLowerCase()}>
    {
        space.imgPath!= null &&
          <Card.Img variant="top" src={space.imgPath} />
    }
    <Card.Header>
      <CardGiftcardIcon /> {' '}
      {space.name}
      <Badge className='float-right' variant='light'><LabelIcon />{space.category}</Badge>
    </Card.Header>
    <Card.Body>
      <Card.Text>
        Location : {space.location} <br />
        Size (WxHxD): 
        {space.sizeWidth!=null?space.sizeWidth:'NA'} x
        {space.sizeHeight!=null?space.sizeHeight:'NA'} x
        {space.sizeDepth!=null?space.sizeDepth:'NA'}
        {space.sizeUnit!=null?' '+space.sizeUnit:''}
      </Card.Text>
      <div>
        <Row>
          <Col xs={7} md={7}>
            {
              tagsArr != null && tagsArr.length > 0 &&
              tagsArr.map((tags, i) => {
                return <span key={i}>
                  <Badge variant='warning'>#{tags}</Badge>
                  {' '}
                </span>
              })
            }
          </Col>
          <Col xs={5} md={5}>
            <ButtonToolbar >
              <IconButton aria-label="select" onClick={() => handleSelect(space.spaceId)}>
                <VisibilityIcon />
              </IconButton>
              <IconButton aria-label="edit" onClick={() => handleEdit(space.spaceId)}>
                <EditIcon />
              </IconButton>
              <IconButton aria-label="delete" onClick={() => handleDelete(space.spaceId)}>
                <DeleteIcon />
              </IconButton>
            </ButtonToolbar>
          </Col>
        </Row>
      </div>
    </Card.Body>
  </Card>
}

function SpaceComp(props){
  const formRef = useRef();
  const handleSubmit = () => {
    if (formRef.current) {
      formRef.current.handleSubmit()
    }
  }

  //generate space data
  let displayList = [];
  if (props.spaceList != null) {
    for (let i = 0; i <= props.spaceList.length - 1; i++) {
      displayList.push(genSpaceData(props.spaceList[i], i, props.handleEdit, props.handleSelect, props.handleDelete));
    }
  }

  return (
    <div>
      <div>
        {
          props.editStatus!==null ? (
            props.editStatus.isSuccess !== null ? (
              props.editStatus.isSuccess === true ? (
                <Alert variant='success'>
                  {props.editStatus.operation} Successefully 
                </Alert>
                  
              ) :
                <Alert variant='danger'>
                  Failed to {props.editStatus.operation}. Error: {props.editStatus.message}
                </Alert>
            ):null
          ):null
        }
      </div>

      {
        //page loading mask
        props.formState.pageLoading === true &&
          <div className="overlay">
            <Spinner animation="border" role="status" size="lg" style={{ width: 10 + 'rem', height: 10 + 'rem' }}
              className='mt-5'>
              <span className="sr-only">Loading...</span>
            </Spinner>
            <h5>Loading...</h5>
          </div>
      }

      {
        // new space button
        props.formState.formMode === Constants.FORM_READONLY_MODE &&
          <Button variant="primary" onClick={props.handleNew}>New Space</Button>
      }

      <CardColumns>
        {displayList}
      </CardColumns>
      <Button variant="primary" onClick={props.handleReloadList}>Refresh</Button>

      <div>
        <Modal 
          show={props.formState.formMode === Constants.FORM_EDIT_MODE} 
          onHide={props.handleCancel}
          dialogClassName="modal-90w"
        >
          <Modal.Header closeButton>
            <Modal.Title>Space Details</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Formik
              enableReinitialize
              initialValues={props.formState}
              validationSchema={validateFormSchema}
              onSubmit={props.handleFormSave}
              innerRef={formRef}
            >
              {({values, errors, touched}) => (
                  <Form>
                    <Row className="justify-content-md-center">
                      <Col xs={12} md={8}>
                        <Field name="imgPath">
                          {({ field, form, meta }) => (
                            field.value != null &&
                            <div>
                              <Image src={field.value} fluid />
                              {
                                form.values.imgPath != null &&
                                <IconButton
                                  aria-label="delete"
                                  className='align-bottom'
                                  onClick={() =>
                                    props.handleRemoveSpaceImg(form.values.spaceId)
                                  }
                                >
                                  <DeleteIcon />
                                </IconButton>
                              }
                            </div>
                          )}
                        </Field>
                      </Col>
                    </Row>
                    <Row>
                      <Col xs={12} md={12}>
                        <label htmlFor="name">Name</label>
                        <Field name="name" type="text" placeholder="Name" className={'form-control' + (errors.name && touched.name ? ' is-invalid' : '')} />
                        <ErrorMessage name="name" component="div" className="invalid-feedback" />
                      </Col>
                    </Row>
                    <Row>
                      <Col xs={12} md={3}>
                        <label htmlFor="location">Location</label>
                        <Field name="location" as="select" placeholder="Location" className={'form-control' + (errors.location && touched.location ? ' is-invalid' : '')}>
                          <option value="">Please select...</option>
                          <option value="Living Room">Living Room</option>
                          <option value="Dinning Room">Dinning Room</option>
                          <option value="Kitechen">Kitechen</option>
                          <option value="Bathroom">Bathroom</option>
                          <option value="Bedroom 1">Bedroom 1</option>
                          <option value="Bedroom 2">Bedroom 2</option>
                          <option value="Bedroom 3">Bedroom 3</option>
                          <option value="Others">Others</option>
                        </Field>
                        <ErrorMessage name="location" component="div" className="invalid-feedback" />
                      </Col>
                      <Col xs={12} md={3}>
                        <label htmlFor="colorCode">Color Code</label>
                        <Field name="colorCode" as="select" placeholder="Color" className={'form-control' + (errors.colorCode && touched.colorCode ? ' is-invalid' : '')}>
                          <option value="">Please select...</option>
                          <option value="Light">Light</option>
                          <option value="Primary">Blue</option>
                          <option value="Secondary">Grey</option>
                          <option value="Success">Green</option>
                          <option value="Danger">Red</option>
                          <option value="Warning">Yellow</option>
                          <option value="Info">Cyan</option>
                        </Field>
                        <ErrorMessage name="colorCode" component="div" className="invalid-feedback" />
                      </Col>
                      <Col xs={12} md={3}>
                        <label htmlFor="tags">Tags</label>
                        <Field name="tags" type="text" placeholder="Use commas to separate Tags" className={'form-control' + (errors.tags && touched.tags ? ' is-invalid' : '')} />
                        <ErrorMessage name="tags" component="div" className="invalid-feedback" />
                      </Col>
                      <Col xs={12} md={3}>
                        <label htmlFor="imgFile">Image</label>
                        <Field name="imgFile">
                          {({ field, form, meta }) => (
                            <input type="file"
                              onChange={event =>
                                form.setFieldValue('imgFile', event.target.files[0])
                              }
                              accept='image/*'
                              className={'form-control' + (errors.imgFile && touched.imgFile ? ' is-invalid' : '')}
                            />
                          )}
                        </Field>
                        <ErrorMessage name="imgFile" component="div" className="invalid-feedback" />
                      </Col>
                    </Row>
                    <Row>
                      
                      <Col xs={12} md={2}>
                        <label htmlFor="sizeWidth">Width</label>
                        <Field name="sizeWidth">
                          {({ field, form, meta }) => (
                            <input type="number" {...field} placeholder="Width" className={'form-control' + (errors.sizeWidth && touched.sizeWidth ? ' is-invalid' : '')} />
                          )}
                        </Field>
                        <ErrorMessage name="sizeWidth" component="div" className="invalid-feedback" />
                      </Col>
                      <Col xs={12} md={2}>
                        <label htmlFor="sizeHeight">Height</label>
                        <Field name="sizeHeight">
                          {({ field, form, meta }) => (
                            <input type="number" {...field} placeholder="Height" className={'form-control' + (errors.sizeHeight && touched.sizeHeight ? ' is-invalid' : '')} />
                          )}
                        </Field>
                        <ErrorMessage name="sizeHeight" component="div" className="invalid-feedback" />
                      </Col>
                      <Col xs={12} md={2}>
                        <label htmlFor="sizeDepth">Depth</label>
                        <Field name="sizeDepth">
                          {({ field, form, meta }) => (
                            <input type="number" {...field} placeholder="Depth" className={'form-control' + (errors.sizeDepth && touched.sizeDepth ? ' is-invalid' : '')} />
                          )}
                        </Field>
                        <ErrorMessage name="sizeDepth" component="div" className="invalid-feedback" />
                      </Col>
                      <Col xs={12} md={2}>
                        <label htmlFor="sizeUnit">Unit</label>
                        <Field name="sizeUnit" as="select" placeholder="Unit" className={'form-control' + (errors.sizeUnit && touched.sizeUnit ? ' is-invalid' : '')}>
                          <option value="">Please select...</option>
                          <option value="cm">cm</option>
                          <option value="m">m</option>
                          <option value="inch">inch</option>
                          <option value="feet">feet</option>
                        </Field>
                        <ErrorMessage name="sizeUnit" component="div" className="invalid-feedback" />
                      </Col>
                    </Row>
                  </Form>
                )}
            </Formik>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={props.handleCancel}>Close</Button>
            <Button id='btnSave' variant="primary" onClick={handleSubmit}>Save changes</Button>
          </Modal.Footer>
        </Modal>
      </div>
    </div>
  );
}

SpaceComp.propTypes = {
  spaceList: PropTypes.array,
  editStatus: PropTypes.object,
  formState: PropTypes.object,
  handleFormSave:PropTypes.func.isRequired,
  handleCancel:PropTypes.func.isRequired,
  handleNew:PropTypes.func.isRequired,
  handleEdit:PropTypes.func.isRequired,
  handleDelete:PropTypes.func.isRequired,
  handleReloadList:PropTypes.func.isRequired,
  handleRemoveSpaceImg:PropTypes.func.isRequired,
}

export default SpaceComp;