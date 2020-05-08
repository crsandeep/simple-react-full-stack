import React from 'react';
import RGL, { WidthProvider } from 'react-grid-layout';
import '../css/react-grid-layout-styles.css';
import '../css/react-resizable-styles.css';
import '../css/SpaceGrid.css';
import PropTypes from 'prop-types';

import {
  Row, Col, ButtonToolbar, Spinner, Alert, Badge, Button
} from 'react-bootstrap';

import { IconButton } from '@material-ui/core/';
import AddCircleOutlineIcon from '@material-ui/icons/AddCircleOutline';
import FormatListBulletedIcon from '@material-ui/icons/FormatListBulleted';
import PostAddIcon from '@material-ui/icons/PostAdd';
import SaveIcon from '@material-ui/icons/Save';
import DeleteIcon from '@material-ui/icons/Delete';
import HighlightOffIcon from '@material-ui/icons/HighlightOff';
import ArrowBackIosIcon from '@material-ui/icons/ArrowBackIos';
import { confirmAlert } from 'react-confirm-alert';
import 'react-confirm-alert/src/react-confirm-alert.css';

import { Prompt } from 'react-router';
import * as Constants from '../constants/Grid';

const ReactGridLayout = WidthProvider(RGL);

function GridComp(props) {
  const confirmDelete = (gridId) => {
    confirmAlert({
      title: 'Confirm to delete',
      message: `Are you sure to delete${gridId > 0 ? ` (ID: ${gridId})` : ''}?`,
      buttons: [
        {
          label: 'Confirm',
          onClick: () => props.handleRemove(gridId)
        },
        {
          label: 'Cancel'
        }
      ]
    });
  };

  return (
    <div>
      <Prompt when={props.isDirtyWrite} message="Changes you made may not be saved. Are you sure you want to leave?" />
      {
        // page loading mask
        props.pageLoading === true && (
          <div className="overlay">
            <Spinner
              animation="border"
              role="status"
              size="lg"
              style={{ width: `${10}rem`, height: `${10}rem` }}
              className="mt-5"
            >
              <span className="sr-only">Loading...</span>
            </Spinner>
            <h5>Loading...</h5>
          </div>
        )
      }

      {props.tempLayouts != null && props.tempLayouts.length > 0 ? (
        <div>
          <Row>
            <Col xs={12} md={12}>
              {props.tempLayouts != null && props.tempLayouts.length === 1 && (parseInt(props.tempLayouts[0].i, 10) < 0) && (
                <Alert variant="success">
                  Ready to manage your space!
                  {' '}
                  Click
                  {' '}
                  <AddCircleOutlineIcon />
                  {' '}
                  to add a new grid.
                </Alert>
              )}
            </Col>
          </Row>
          <Row>
            <Col xs={12} md={1}>
              <IconButton
                aria-label="delete"
                onClick={() => props.handleGoBack()}
              >
                <ArrowBackIosIcon />
              </IconButton>
            </Col>
            <Col xs={12} md={2} className="spaceGrid-changeMode">
              <div>
                Current Mode:
                {' '}
                <select
                  value={props.currMode}
                  onChange={(event) => {
                    props.handleToggleMode(event.target.value);
                  }}
                >
                  <option value={Constants.FORM_READONLY_MODE}>View</option>
                  <option value={Constants.FORM_EDIT_MODE}>Edit</option>
                </select>
              </div>
            </Col>
            <Col xs={12} md={9}>
              <ButtonToolbar>
                <IconButton aria-label="New" onClick={props.handleNew}>
                  <AddCircleOutlineIcon />
                </IconButton>
                <IconButton aria-label="Save" onClick={props.handleSave}>
                  <SaveIcon />
                </IconButton>
                <IconButton aria-label="Cancel" onClick={props.handleCancel}>
                  <HighlightOffIcon />
                </IconButton>
              </ButtonToolbar>
            </Col>

          </Row>
          <Row>
            <Col xs={12} md={12}>
              {
                props.displayMsg.isSuccess !== null ? (
                  props.displayMsg.isSuccess === true ? (
                    <Alert variant="success">
                      {props.displayMsg.msg}
                    </Alert>
                  )
                    : (
                      <Alert variant="danger">
                        {props.displayMsg.msg}
                      </Alert>
                    )
                ) : null
              }
            </Col>
          </Row>
          <Row>
            <Col xs={12} md={12}>
              <ReactGridLayout
                cols={12}
                rowHeight={120}
                layout={props.tempLayouts}
                onLayoutChange={props.handleUpdateLayout}
              >
                {props.tempLayouts !== null
                  && props.tempLayouts.map(grid => (
                    <div
                      key={grid.i}
                      className={
                        grid.static ? 'spaceGrid-grid-static' : 'spaceGrid-grid'
                      }
                      style={props.gridImgPath != null ? { backgroundImage: `url(${props.gridImgPath})` } : ''}
                    >
                      {
                        // generate ID panel
                        parseInt(grid.i, 10) > 0 ? (
                          <h3 className="spaceGrid-idPanel">{grid.i.padStart(2, '0').slice(-3)}</h3>
                        ) : (
                          <h3 className="spaceGrid-newIdPanel">{`New ${(Math.abs(grid.i) - 1).toString().padStart(2, '0')}`}</h3>
                        )
                      }

                      {
                        // edit mode - drag item message
                        props.currMode === Constants.FORM_EDIT_MODE // under edit mode
                        && (
                          <h3 className="spaceGrid-dragTips">Drag & Organise</h3>
                        )
                      }

                      <ButtonToolbar>
                        { // go to item page button
                          props.currMode === Constants.FORM_READONLY_MODE // under readonly mode
                          && parseInt(grid.i, 10) > 0 // old grid
                            && (
                            <Button variant="outline-info" size="lg" block onClick={() => props.handleSelect(grid.i)}>

                              {props.dataMap.get(grid.i).itemCount === 0 ? (
                                <div>
                                  <PostAddIcon />
                                  Add items
                                </div>
                              ) : (
                                <div>
                                  <FormatListBulletedIcon />
                                  {props.dataMap.get(grid.i).itemCount}
                                  {' '}
                                  Items
                                </div>
                              )}

                            </Button>
                            )
                        }
                      </ButtonToolbar>

                      {
                        // item tags
                        props.dataMap != null
                        && props.dataMap.get(grid.i) != null
                        && props.dataMap.get(grid.i).tagList.map(tag => (
                          <span key={`${grid.i}-${tag}`}>
                            <Badge variant="warning">
                              #
                              {tag}
                            </Badge>
                            {' '}
                          </span>
                        ))
                      }
                      <ButtonToolbar className="spaceGrid-editPanel">
                        {
                          // delete grid button
                          props.currMode === Constants.FORM_EDIT_MODE // under edit mode
                          && (
                            parseInt(grid.i, 10) < 0 // new grid, not yet save
                            || (
                              props.dataMap != null && props.dataMap.get(grid.i) != null // old grid, no item in grid
                              && props.dataMap.get(grid.i).itemCount === 0
                            )
                          )
                            ? (
                              <IconButton
                                aria-label="delete"
                                onClick={() => confirmDelete(grid.i)}
                              >
                                <DeleteIcon />
                              </IconButton>
                            ) : null
                        }

                      </ButtonToolbar>
                    </div>
                  ))
                }

              </ReactGridLayout>
            </Col>
          </Row>
        </div>
      ) : (
        <Alert variant="info">
          Please select your space from left side menu!
        </Alert>
      )}
    </div>
  );
}

GridComp.defaultProps = {
  gridImgPath: null
};

GridComp.propTypes = {
  displayMsg: PropTypes.oneOfType([PropTypes.object]).isRequired,
  pageLoading: PropTypes.bool.isRequired,
  tempLayouts: PropTypes.arrayOf(PropTypes.object).isRequired,
  dataMap: PropTypes.oneOfType([PropTypes.object]).isRequired,
  isDirtyWrite: PropTypes.bool.isRequired,
  currMode: PropTypes.string.isRequired,
  gridImgPath: PropTypes.string,
  handleNew: PropTypes.func.isRequired,
  handleToggleMode: PropTypes.func.isRequired,
  handleSave: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  handleUpdateLayout: PropTypes.func.isRequired,
  handleRemove: PropTypes.func.isRequired,
  handleSelect: PropTypes.func.isRequired,
  handleGoBack: PropTypes.func.isRequired
};

export default GridComp;
