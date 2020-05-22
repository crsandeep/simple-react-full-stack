import React from 'react';
import RGL, { WidthProvider } from 'react-grid-layout';
import '../css/react-grid-layout-styles.css';
import '../css/react-resizable-styles.css';
import '../css/SpaceGrid.css';
import PropTypes from 'prop-types';

import {
  Row, Col, ButtonToolbar, Alert, Badge, Button, OverlayTrigger, Tooltip
} from 'react-bootstrap';

import { IconButton } from '@material-ui/core/';
import FormatListBulletedIcon from '@material-ui/icons/FormatListBulleted';
import PostAddIcon from '@material-ui/icons/PostAdd';
import SaveIcon from '@material-ui/icons/Save';
import DeleteIcon from '@material-ui/icons/Delete';
import HighlightOffIcon from '@material-ui/icons/HighlightOff';
import AddCircleOutlineIcon from '@material-ui/icons/AddCircleOutline';
import ArrowBackIosIcon from '@material-ui/icons/ArrowBackIos';

import FormControlLabel from '@material-ui/core/FormControlLabel';
import Switch from '@material-ui/core/Switch';

import { Prompt } from 'react-router';
import * as Constants from '../constants/Grid';
import * as UIConstants from '../constants/Global';
import BaseUIComp from './BaseUIComp';

const ReactGridLayout = WidthProvider(RGL);

function GridComp(props) {
  const isLargeScreen = (window.innerWidth > UIConstants.UI_SMALL_SCREEN_WIDTH);

  const renderTagsTooltip = (prop, text) => (
    <Tooltip id="button-tooltip" {...prop}>
      {text}
    </Tooltip>
  );

  // hook for switch view
  const [state, setState] = React.useState({
    isEditMode: false
  });
  const handleChange = (event) => {
    setState({ ...state, [event.target.name]: event.target.checked });
    props.handleToggleMode(event.target.checked ? Constants.FORM_EDIT_MODE : Constants.FORM_READONLY_MODE);
  };


  return (
    <div>
      <Prompt when={props.isDirtyWrite} message="Changes you made may not be saved. Are you sure you want to leave?" />

      <BaseUIComp
        displayMsg={props.displayMsg}
        pageLoading={props.pageLoading}
      />

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
            <Col xs={6} md={4}>
              <IconButton
                aria-label="back"
                onClick={() => props.handleGoBack()}
              >
                <ArrowBackIosIcon />
              </IconButton>
              <FormControlLabel
                control={(
                  <Switch
                    checked={state.isListView}
                    onChange={handleChange}
                    name="isEditMode"
                    color="primary"
                  />
                )}
                label="Edit"
              />
            </Col>
            <Col xs={6} md={8}>
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
              <ReactGridLayout
                cols={4}
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
                          <h4 className={isLargeScreen ? 'spaceGrid-dragTips' : 'spaceGrid-dragTips-mobile'}>
                            Drag & Organise

                          </h4>
                        )
                      }

                      <div className="spaceGrid-manageBtnPanel">
                        { // go to item page button
                          props.currMode === Constants.FORM_READONLY_MODE // under readonly mode
                          && parseInt(grid.i, 10) > 0 // old grid
                            && (
                            <Button
                              variant="outline-dark"
                              className="spaceGrid-manageBtnPanel"
                              onClick={() => props.handleSelect(parseInt(grid.i, 10))}
                              {...(isLargeScreen ? { size: 'lg', block: 'block' } : null)}
                            >

                              {props.dataMap.get(grid.i).itemCount === 0 ? (
                                <div>
                                  <PostAddIcon />
                                  Add
                                  {isLargeScreen ? ' items' : null}
                                </div>
                              ) : (
                                <div>
                                  <FormatListBulletedIcon />
                                  {props.dataMap.get(grid.i).itemCount}
                                  {isLargeScreen ? ' items' : null}
                                </div>
                              )}

                            </Button>
                            )
                        }
                      </div>

                      {
                        // item tags
                        props.dataMap != null
                        && props.dataMap.get(grid.i) != null
                        && props.dataMap.get(grid.i).itemTags.map((tag, i) => (
                          i === grid.w * (isLargeScreen ? 3 : 1) - 1 ? (
                            // small screen and last displayable tags
                            <span key={`${grid.i}-${tag}`}>
                              <OverlayTrigger
                                placement="right"
                                delay={{ show: 250, hide: 400 }}
                                overlay={prop => renderTagsTooltip(prop, `#${props.dataMap.get(grid.i).itemTags.slice(i).join(', #')}`)}
                              >
                                <Badge variant="success">
                                  {props.dataMap.get(grid.i).itemTags.length - i}
                                  + tags
                                </Badge>
                              </OverlayTrigger>

                            </span>
                          ) : i >= grid.w * (isLargeScreen ? 3 : 1) ? null : (
                            // large screen + small screen < grid width
                            <span key={`${grid.i}-${tag}`}>
                              <Badge variant="warning">
                                #
                                {tag}
                              </Badge>
                              {' '}
                            </span>
                          )
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
                                onClick={() => props.handleRemove(grid.i)}
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
