import React, { useRef } from 'react';
import PropTypes from 'prop-types';
import {
  ListItemSecondaryAction, List, ListItem, ListItemText, ListSubheader,
  IconButton, Box, ListItemIcon, Avatar, Typography, Divider
} from '@material-ui/core/';
import {
  Add, Cached, Delete, Edit, SingleBed, KingBed, LocalHotel,
  Wc, Fastfood, Kitchen, Weekend, HelpOutline
} from '@material-ui/icons';
import {
  Button, Modal, Row, Col, Image, Badge
} from 'react-bootstrap';
import {
  Formik, Field, Form, ErrorMessage
} from 'formik';
import * as Yup from 'yup';

import * as Constants from '../constants/Space';
import BaseUIComp from './BaseUIComp';

// css
import '../css/Form.css';
import '../css/Split.css';
import '../css/SpaceList.css';

const validateFormSchema = Yup.object().shape({
  name: Yup.string()
    .required('Name is required')
    .min(3, 'Name must be at least 3 characters')
    .trim(),
  location: Yup.string()
    .required('Location is required')
    .min(1, 'Please select location')
});


function SpaceComp(props) {
  const formRef = useRef();
  const handleSubmit = () => {
    if (formRef.current) {
      formRef.current.handleSubmit();
    }
  };

  // generate left side list bar
  const handleSpaceClick = (event, index) => {
    props.handleSelect(index);
  };

  const getSpaceItem = (spaceList, handleEdit, handleSelect, handleDelete) => {
    const itemList = [];

    for (const space of spaceList) {
      itemList.push(
        <ListItem
          key={space.spaceId}
          alignItems="flex-start"
          button
          // selected={selectedSpace === space.spaceId}
          onClick={event => handleSpaceClick(event, space.spaceId)}
        >
          <ListItemIcon>
            {space.imgPath != null ? (
              <img src={space.imgPath} alt={space.name} className="spaceList-itemImage" />
            ) : (
              <Avatar variant="rounded" alt={space.name}>
                {
                  space.name.substring(0, 4)
                }
              </Avatar>
            )}
          </ListItemIcon>
          <ListItemText
            primary={space.name}
            secondary={(
              <React.Fragment>
                <Typography
                  component="span"
                  variant="body2"
                  className="spaceList-inline"
                  color="textSecondary"
                >
                  {`Grids: ${space.gridCount} - Items: ${space.itemCount}`}
                </Typography>
                <br />
                {
                  space.itemTags.map(tag => (
                    <Badge key={tag} variant="warning">
                      {tag}
                    </Badge>
                  ))
                }
              </React.Fragment>
            )}
          />
          <ListItemSecondaryAction>
            <IconButton
              aria-label="edit"
              onClick={() => handleEdit(space.spaceId)}
            >
              <Edit />
            </IconButton>
            <IconButton
              aria-label="delete"
              onClick={() => handleDelete(space.spaceId, space.name)}
            >
              <Delete />
            </IconButton>
          </ListItemSecondaryAction>
        </ListItem>
      );
    }
    return itemList;
  };

  const genSpaceList = (spaceList, handleEdit, handleSelect, handleDelete) => {
    const displayList = [];
    const spaceMap = new Map();
    let tempList = null;

    // prepare Map<Location,List<Space>> for further generation
    for (const space of spaceList) {
      // get corresponding list
      if (spaceMap.get(space.location) != null) {
        tempList = spaceMap.get(space.location);
      } else {
        tempList = [];
      }

      // // add to list
      tempList.push(space);

      // update map with latest list
      spaceMap.set(space.location, tempList);
    }

    // generate header and related spaces under each location according to Map settings
    for (const [location, list] of spaceMap) {
      displayList.push(
        <li key={`section-${location}`}>
          <ul className="spaceList-ul">
            <ListSubheader>
              {
                {
                  'Bedroom 1': <SingleBed />,
                  'Bedroom 2': <LocalHotel />,
                  'Bedroom 3': <KingBed />,
                  'Living Room': <Weekend />,
                  'Dinning Room': <Fastfood />,
                  Kitechen: <Kitchen />,
                  Bathroom: <Wc />,
                  Others: <HelpOutline />
                }[location]
              }
              {' '}
              {location}
            </ListSubheader>
            {getSpaceItem(list, handleEdit, handleSelect, handleDelete)}
          </ul>
        </li>
      );
    }
    return displayList;
  };

  // list mode
  let dataList = [];
  if (props.spaceList != null && props.spaceList.length > 0) {
    dataList = genSpaceList(
      props.spaceList,
      props.handleEdit,
      props.handleSelect,
      props.handleDelete
    );
  }

  return (
    <div>
      <BaseUIComp
        displayMsg={props.displayMsg}
        pageLoading={props.pageLoading}
      />

      <Row>
        <Col xs={12} md={12}>
          <Box display="flex" justifyContent="flex-end">
            {
              // new space button
              props.formState.formMode === Constants.FORM_READONLY_MODE && (
                <IconButton
                  aria-label="Add"
                  onClick={props.handleNew}
                >
                  <Add />
                </IconButton>
              )
            }

            <IconButton
              aria-label="refresh"
              onClick={props.handleReloadList}
            >
              <Cached />
            </IconButton>
          </Box>
          <Divider />
        </Col>
      </Row>

      <List className="spaceList-pc" subheader={<li />}>
        {dataList}
      </List>

      <div>
        <Modal
          show={props.formState.formMode === Constants.FORM_EDIT_MODE}
          onHide={props.handleCancel}
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
              {({ errors, touched }) => (
                <Form>
                  <Row className="justify-content-md-center">
                    <Col xs={12} md={12}>
                      <Field name="imgPath">
                        {
                          ({ field, form }) => field.value != null && (
                            <div>
                              <Image src={field.value} className="modal-lg-image" fluid />
                              {form.values.imgPath != null && (
                              <IconButton
                                aria-label="delete"
                                className="align-bottom"
                                onClick={() => props.handleRemoveSpaceImg(
                                  form.values.spaceId
                                )
                                      }
                              >
                                <Delete />
                              </IconButton>
                              )}
                            </div>
                          )
                        }
                      </Field>
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={12}>
                      <label htmlFor="name" className="required-field">Space Name</label>
                      <Field
                        id="name"
                        name="name"
                        type="text"
                        placeholder="Name"
                        className={`form-control${
                          errors.name && touched.name ? ' is-invalid' : ''
                        }`}
                      />
                      <ErrorMessage
                        name="name"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={5}>
                      <label htmlFor="location" className="required-field">Space Location</label>
                      <Field
                        name="location"
                        as="select"
                        placeholder="Location"
                        className={`form-control${
                          errors.location && touched.location
                            ? ' is-invalid'
                            : ''
                        }`}
                      >
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
                      <ErrorMessage
                        name="location"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                    <Col xs={12} md={7}>
                      <label htmlFor="imgFile">Display Image</label>
                      <Field name="imgFile">
                        {({ form }) => (
                          <input
                            type="file"
                            onChange={event => form.setFieldValue(
                              'imgFile',
                              event.target.files[0]
                            )
                            }
                            accept="image/*"
                            className={`form-control${
                              errors.imgFile && touched.imgFile
                                ? ' is-invalid'
                                : ''
                            }`}
                          />
                        )}
                      </Field>
                      <ErrorMessage
                        name="imgFile"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                  </Row>
                </Form>
              )}
            </Formik>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={props.handleCancel}>
              Close
            </Button>
            <Button id="btnSave" variant="primary" onClick={handleSubmit}>
              Save changes
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    </div>
  );
}
SpaceComp.defaultProps = {
  spaceList: []
};

SpaceComp.propTypes = {
  displayMsg: PropTypes.oneOfType([PropTypes.object]).isRequired,
  spaceList: PropTypes.arrayOf(PropTypes.object),
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  pageLoading: PropTypes.bool.isRequired,
  handleFormSave: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  handleNew: PropTypes.func.isRequired,
  handleEdit: PropTypes.func.isRequired,
  handleDelete: PropTypes.func.isRequired,
  handleReloadList: PropTypes.func.isRequired,
  handleRemoveSpaceImg: PropTypes.func.isRequired,
  handleSelect: PropTypes.func.isRequired
};

export default SpaceComp;
